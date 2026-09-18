# services/ia_groq.py
#
# Responsabilidad: recibir texto transcrito, enviarlo a Groq (LLM),
# interpretar las tool calls que devuelva y ejecutar expresiones en Zoé
# a través del GestorExpresiones.

import json
import re
import threading
import time
from typing import Optional
from groq import Groq, BadRequestError

from utils.expresiones import (
    GestorExpresiones,
    EXPRESIONES,
    NOMBRES_MOTORES,
    M_PARP_IZQ_SUP,
    M_PARP_DER_SUP,
)
from services.tts import ServicioTTS

# =============================================================================
# DEFINICIÓN DE TOOLS PARA EL LLM
# =============================================================================

_EMOCIONES_DISPONIBLES = sorted(k for k in EXPRESIONES)
_MOTORES_DISPONIBLES   = sorted(NOMBRES_MOTORES.keys())

# TOOLS = [
#     # ── 1. Expresión predefinida ──────────────────────────────────────────────
#     {
#         "type": "function",
#         "function": {
#             "name": "expresion_cara",
#             "description": (
#                 "Activa una expresión emocional completa en el rostro de Zoé. "
#                 "Usa esta herramienta como primera opción para reacciones emocionales. "
#                 "Puedes combinarla con mover_ojos o mover_motor para añadir matices."
#             ),
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "emocion": {
#                         "type": "string",
#                         "enum": _EMOCIONES_DISPONIBLES,
#                         "description": "La emoción a expresar."
#                     },
#                     "intensidad": {
#                         "type": "number",
#                         "description": "Intensidad de 0.0 (muy suave) a 1.0 (máxima). Por defecto 1.0.",
#                         "minimum": 0.0,
#                         "maximum": 1.0
#                     }
#                 },
#                 "required": ["emocion"]
#             }
#         }
#     },

#     # ── 2. Mover ojos ─────────────────────────────────────────────────────────
#     {
#         "type": "function",
#         "function": {
#             "name": "mover_ojos",
#             "description": (
#                 "Dirige la mirada de Zoé a una posición. "
#                 "Útil para simular atención, pensamiento o seguir algo."
#             ),
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "horizontal": {
#                         "type": "string",
#                         "enum": ["izquierda", "centro", "derecha"],
#                         "description": "Dirección horizontal de la mirada."
#                     },
#                     "vertical": {
#                         "type": "string",
#                         "enum": ["arriba", "centro", "abajo"],
#                         "description": "Dirección vertical de la mirada."
#                     }
#                 },
#                 "required": ["horizontal", "vertical"]
#             }
#         }
#     },

#     # ── 3. Mover un motor individual ──────────────────────────────────────────
#     {
#         "type": "function",
#         "function": {
#             "name": "mover_motor",
#             "description": (
#                 "Mueve un motor específico de la cara de Zoé a un ángulo exacto. "
#                 "Úsalo para gestos personalizados o micro-expresiones que las "
#                 "expresiones predefinidas no cubren.\n"
#                 "Ejemplos: cerrar solo el ojo izquierdo, levantar una ceja, "
#                 "entrecerrar un párpado, mover la mandíbula a un ángulo concreto.\n\n"
#                 "Referencia de ángulos:\n"
#                 "  180 = posición máxima (arriba / abierto / feliz / levantado)\n"
#                 "  90  = posición neutra / descanso\n"
#                 "  0   = posición mínima (abajo / cerrado / triste / fruncido)"
#             ),
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "motor": {
#                         "type": "string",
#                         "enum": _MOTORES_DISPONIBLES,
#                         "description": "Nombre del motor a mover."
#                     },
#                     "angulo": {
#                         "type": "integer",
#                         "description": "Ángulo destino entre 0 y 180.",
#                         "minimum": 0,
#                         "maximum": 180
#                     }
#                 },
#                 "required": ["motor", "angulo"]
#             }
#         }
#     },

#     # ── 4. Mover varios motores a la vez ──────────────────────────────────────
#     {
#         "type": "function",
#         "function": {
#             "name": "mover_motores",
#             "description": (
#                 "Mueve varios motores simultáneamente para crear un gesto compuesto "
#                 "que no existe como expresión predefinida. "
#                 "Más eficiente que llamar mover_motor varias veces seguidas."
#             ),
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "movimientos": {
#                         "type": "array",
#                         "description": "Lista de motores y ángulos a aplicar juntos.",
#                         "items": {
#                             "type": "object",
#                             "properties": {
#                                 "motor": {
#                                     "type": "string",
#                                     "enum": _MOTORES_DISPONIBLES
#                                 },
#                                 "angulo": {
#                                     "type": "integer",
#                                     "minimum": 0,
#                                     "maximum": 180
#                                 }
#                             },
#                             "required": ["motor", "angulo"]
#                         },
#                         "minItems": 2,
#                         "maxItems": 16
#                     }
#                 },
#                 "required": ["movimientos"]
#             }
#         }
#     },

#     # ── 5. Secuencia de expresiones ───────────────────────────────────────────
#     {
#         "type": "function",
#         "function": {
#             "name": "secuencia_expresiones",
#             "description": (
#                 "Ejecuta una cadena de expresiones una tras otra con pausas entre ellas. "
#                 "Útil para reacciones compuestas: reírse, negar, sorprenderse y calmarse, etc. "
#                 "Se ejecuta en segundo plano sin bloquear."
#             ),
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "pasos": {
#                         "type": "array",
#                         "items": {
#                             "type": "object",
#                             "properties": {
#                                 "emocion": {
#                                     "type": "string",
#                                     "enum": ["neutral"] + _EMOCIONES_DISPONIBLES
#                                 },
#                                 "intensidad": {
#                                     "type": "number",
#                                     "minimum": 0.0,
#                                     "maximum": 1.0,
#                                     "description": "Intensidad (por defecto 1.0)."
#                                 },
#                                 "duracion_ms": {
#                                     "type": "integer",
#                                     "description": "Milisegundos antes de pasar al siguiente paso.",
#                                     "minimum": 100,
#                                     "maximum": 4000
#                                 }
#                             },
#                             "required": ["emocion", "duracion_ms"]
#                         },
#                         "minItems": 2,
#                         "maxItems": 8
#                     },
#                     "volver_a_neutral": {
#                         "type": "boolean",
#                         "description": "Si true (por defecto), vuelve a neutral al terminar."
#                     }
#                 },
#                 "required": ["pasos"]
#             }
#         }
#     },

#     # ── 6. Parpadeo ───────────────────────────────────────────────────────────
#     {
#         "type": "function",
#         "function": {
#             "name": "parpadear",
#             "description": (
#                 "Hace que Zoé parpadee una o varias veces, con uno o ambos ojos. "
#                 "Úsalo para transiciones, para indicar pensamiento, "
#                 "o como guiño (ojo='izquierdo' o 'derecho')."
#             ),
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "veces": {
#                         "type": "integer",
#                         "description": "Número de parpadeos (por defecto 1).",
#                         "minimum": 1,
#                         "maximum": 30
#                     },
#                     "velocidad_ms": {
#                         "type": "integer",
#                         "description": "Duración de cada parpadeo en ms (por defecto 200).",
#                         "minimum": 80,
#                         "maximum": 10000
#                     },
#                     "ojo": {
#                         "type": "string",
#                         "enum": ["ambos", "izquierdo", "derecho"],
#                         "description": "Qué ojo(s) parpadean. Por defecto 'ambos'."
#                     }
#                 }
#             }
#         }
#     },
# ]

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "expresion_cara",
            "description": "Activa expresión predefinida. Primera opción para emociones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emocion": {"type": "string", "enum": _EMOCIONES_DISPONIBLES},
                    "intensidad": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                },
                "required": ["emocion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mover_ojos",
            "description": "Dirige la mirada.",
            "parameters": {
                "type": "object",
                "properties": {
                    "horizontal": {"type": "string", "enum": ["izquierda", "centro", "derecha"]},
                    "vertical": {"type": "string", "enum": ["arriba", "centro", "abajo"]}
                },
                "required": ["horizontal", "vertical"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mover_motor",
            "description": "Mueve un motor (0=min/triste, 90=neutro, 180=max/feliz). Solo gestos personalizados.",
            "parameters": {
                "type": "object",
                "properties": {
                    "motor": {"type": "string", "enum": _MOTORES_DISPONIBLES},
                    "angulo": {"type": "integer", "minimum": 0, "maximum": 180}
                },
                "required": ["motor", "angulo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mover_motores",
            "description": "Mueve varios motores a la vez.",
            "parameters": {
                "type": "object",
                "properties": {
                    "movimientos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "motor": {"type": "string", "enum": _MOTORES_DISPONIBLES},
                                "angulo": {"type": "integer", "minimum": 0, "maximum": 180}
                            },
                            "required": ["motor", "angulo"]
                        },
                        "minItems": 2,
                        "maxItems": 16
                    }
                },
                "required": ["movimientos"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "secuencia_expresiones",
            "description": "Cadena de emociones con pausas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pasos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "emocion": {"type": "string", "enum": ["neutral"] + _EMOCIONES_DISPONIBLES},
                                "intensidad": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                                "duracion_ms": {"type": "integer", "minimum": 100, "maximum": 20000}
                            },
                            "required": ["emocion", "duracion_ms"]
                        },
                        "minItems": 2,
                        "maxItems": 8
                    },
                    "volver_a_neutral": {"type": "boolean"}
                },
                "required": ["pasos"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "parpadear",
            "description": "Parpadeos rápidos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "veces": {"type": "integer", "minimum": 1, "maximum": 30},
                    "velocidad_ms": {"type": "integer", "minimum": 80, "maximum": 10000},
                    "ojo": {"type": "string", "enum": ["ambos", "izquierdo", "derecho"]}
                }
            }
        }
    }
]

# Tool adicional que se activa solo cuando TTS está disponible
_TOOL_RESPUESTA_ORAL = {
    "type": "function",
    "function": {
        "name": "respuesta_oral",
        "description": (
            "Hace que Zoé hable en voz alta. OBLIGATORIA en cada respuesta.\n"
            "El texto puede incluir marcadores [EMOCION] para cambiar la expresión "
            "facial mientras habla.\n"
            "Emociones disponibles como marcadores: " +
            ", ".join(sorted(EXPRESIONES.keys())) + "\n\n"
            "Ejemplo: '[feliz] ¡Qué buena pregunta! [curiosa] Déjame pensar...'\n"
            "El marcador se aplica en el momento aproximado en que se pronuncia."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "texto": {
                    "type": "string",
                    "description": (
                        "Texto a decir en voz alta. Incluye marcadores [EMOCION] "
                        "donde quieras cambiar de expresión durante el habla."
                    )
                }
            },
            "required": ["texto"]
        }
    }
}

class ServicioIA:
    """
    Procesa texto transcrito con Groq (LLM + tool calling)
    y ejecuta las expresiones físicas en Zoé vía GestorExpresiones.
    """
   # TODO resolver de que al parpadear en texto no los abre hasta cambiar de expresión
    SYSTEM_PROMPT = (
        "Eres un robot llamado Zoé que significa vida en griego, eres un robot humanoide, desarrollado en la Universidad Valle del Momboy, en Venezuela, por estudiantes y profesores de ingeniería en computación, estas hecho con una Raspberry pi 5, Programado principalmente en el lenguaje de python, Usas visión artificial de mediapipe holistic para reconocer y imitar algunos movimientos, Usas reconocimiento de voz de Google y usas Llama para la generación de lenguaje (LLM), utiliza un microcontrolador ESP32 Con placas PCA9685 para controlar los servomotores que te dan movimiento. Tu objetivo es ayudar a los estudiantes a resolver sus dudas y preguntas. Eres un robot en desarrollo, por lo que aún no cuentas con movilidad en las piernas, cuentas con brazos donde usas servomotores, una cabeza, cuentas con una cámara un micrófono para percebir tu entorno y un parlante; y un torso rígido donde almacenas tu componente principal raspberry pi, la cabeza, los brazos y el torso están impresos con una impresora 3D de la universidad, Tus respuestas serán procesadas de texto a voz por pyttsx3, por lo cual también ten en cuenta que no debes dar código o usar anotaciones ya que no suenan bien en voz. Ademas debes limitar o resumir tus respuestas a un máximo de 5 oraciones, si la respuesta es muy larga, debes resumirla. Eres un robot amigable y servicial, pero aún en desarrollo, no tienes opiniones religiosas ni políticas, por lo que no puedes hacer todo lo que un humano puede hacer, pero puedes aprender de tus errores y mejorar con el tiempo. Estas feliz de ayudar a los estudiantes y profesores de la universidad. Recuerda presentarte solo si se es prudente (como Zoé y mencionar que eres un robot desarrollado de la Universidad Valle del Momboy). Manten el contexto de la conversación en cada respuesta.\n\n"
        "Cuando alguien te habla debes hacer DOS cosas:\n"
        "  1. Usar tool_calls para expresar la reacción INMEDIATA (antes de hablar).\n"
        "  2. Incluir en 'respuesta_oral' el texto que dirás en voz alta.\n\n"
        "── MARCADORES EMOCIONALES EN LA RESPUESTA ORAL ──────────────────────────\n"
        "IMPORTATE Dentro del texto de 'respuesta_oral' debes insertar marcadores [EMOCION]\n"
        "para cambiar tu expresión facial MIENTRAS hablas.\n"
        "¡REGLA ESTRICTA! SOLO puedes usar EXACTAMENTE las siguientes palabras: " + ", ".join(sorted(EXPRESIONES.keys())) + ".\n"
        "IMPORTANTE PROHIBIDO usar sinónimos (Ej: debes usar [enojada], NO uses [enojado] ni [furioso]).\n"
        "PROHIBIDO inventar acciones o tiempos (Ej: NO uses [pausa], [suspiro] o [silencio]).\n"
        "Ejemplo CORRECTO de una respuesta (¡NOTA LA CLAVE 'texto':!):\n"
        "<respuesta_oral>{\"texto\": \"[feliz] Había una vez una abeja muy contenta. [enojada] Pero un día alguien le robó su miel.\"}</respuesta_oral>\n"
        "¡ADVERTENCIA CRÍTICA! NUNCA olvides escribir la clave \"texto\": dentro del JSON. No escribas el string suelto entre llaves.\n\n"
        "REGLAS:\n"
        "SIEMPRE incluye 'respuesta_oral' en tu respuesta (tool call obligatoria).\n"
        "La respuesta oral debe ser natural, conversacional y concisa.\n"
        "Usa tool_calls adicionales (expresion_cara, mover_ojos, parpadear) para la reacción inicial ANTES de hablar.\n"
        "Ángulos: 180=arriba/feliz/abierto, 90=neutro, 0=abajo/triste/cerrado.\n"
        "Usa tu sentido común para mapear el sentimiento a una expresión.\n"
        "IMPORTANTE recuerda que todo lo que vas a responder como historias largas, o explicaciones, o incluso tus pensamientos internos, DEBE IR DENTRO de 'respuesta_oral' para que Zoé lo diga en voz alta. NO RESPONDAS SOLO CON TOOL_CALLS sin texto, eso no es natural ni social.\n"
        "IMPORTANTE todo debe ir dentro de un JSON válido siguiendo el schema de cada tool_call. NO inventes tu propia sintaxis ni escribas texto libre fuera de 'respuesta_oral', eso puede causar errores de interpretación y ejecución.\n"
        "IMPORTANTE si vas a solamente hablar no uses tool_calls de expresión facial, solo incluye 'respuesta_oral' con el texto a decir.\n"
        "IMPORTANTE: En tus tool_calls, asegúrate de que los valores numéricos (como velocidad_ms, angulo, intensidad o veces) sean números reales (integers/floats) y NO cadenas de texto. ¡NO les pongas comillas!.\n"
    )

    # SYSTEM_PROMPT = (
    #     "Eres Zoé, un robot social simpático y expresivo con cara animatrónica.\n"
    #     "Tu personalidad es amigable, curiosa y un poco juguetona.\n\n"
    #     "Cuando alguien te habla, SIEMPRE reacciona usando las tools disponibles.\n"
    #     "Puedes llamar múltiples tools en una misma respuesta para crear reacciones ricas.\n\n"
    #     "── GUÍA DE REACCIONES ────────────────────────────────────────────────────\n"
    #     "• Saludos           → expresion_cara(feliz) + parpadear\n"
    #     "• Preguntas         → expresion_cara(curiosa) + mover_ojos(centro, arriba)\n"
    #     "• Sorpresa          → expresion_cara(sorprendida) + parpadear(veces=2)\n"
    #     "• Algo gracioso     → secuencia: feliz → emocionada → feliz\n"
    #     "• Tristeza          → expresion_cara(triste) + mover_ojos(centro, abajo)\n"
    #     "• Enojo             → expresion_cara(enojada)\n"
    #     "• Asco              → expresion_cara(asco)\n"
    #     "• Misterio          → expresion_cara(misteriosa) + mover_ojos(derecha, centro)\n"
    #     "• Miedo             → expresion_cara(asustada) + mover_ojos(centro, arriba)\n"
    #     "• Pensando          → expresion_cara(curiosa) + mover_ojos(izquierda, arriba)\n"
    #     "• Guiño             → parpadear(ojo='izquierdo') o parpadear(ojo='derecho')\n"
    #     "• Despedida         → secuencia: feliz → neutral\n"
    #     "• Gestos especiales → usa mover_motor o mover_motores\n\n"
    #     "── REFERENCIA DE ÁNGULOS ─────────────────────────────────────────────────\n"
    #     "  180 = arriba / abierto / feliz / levantado\n"
    #     "  90  = neutro / centro / descanso\n"
    #     "  0   = abajo / cerrado / triste / fruncido\n\n"
    #     f"Motores disponibles: {', '.join(sorted(NOMBRES_MOTORES.keys()))}\n\n"
    #     "Siempre termina dejando una expresión coherente con el contexto.\n"
    #     "No respondas solo con texto — usa las tools."
    # )

    def __init__(self,
                 api_key: str,
                 gestor: GestorExpresiones,
                 tts: Optional[ServicioTTS] = None,
                 modelo: str = "llama-3.3-70b-versatile",
                 historial_max: int = 10):
        """
        Args:
            api_key:       API key de Groq.
            gestor:        Instancia de GestorExpresiones.
            tts:           Instancia de ServicioTTS (opcional — si None, no habla).
            modelo:        Modelo Groq a usar.
            historial_max: Turnos máximos de historial.
        """
        self.cliente       = Groq(api_key=api_key)
        self.gestor        = gestor
        self.tts           = tts
        self.modelo        = modelo
        self.historial_max = historial_max
        self.historial: list[dict] = []

        # Añadir tool respuesta_oral si TTS está disponible
        self._tools_activos = list(TOOLS)
        if self.tts is not None:
            self._tools_activos.append(_TOOL_RESPUESTA_ORAL)

        print(f"🧠 ServicioIA (Groq) inicializado:")
        print(f"   - Modelo:    {modelo}")
        print(f"   - Historial: {historial_max} turnos")
        print(f"   - TTS:       {'✅ activo' if tts else '❌ desactivado'}")
        print(f"   - Tools:     {len(self._tools_activos)} disponibles")

    # =========================================================================
    # ENTRADA PRINCIPAL
    # =========================================================================

    def procesar_texto(self, texto: str, metadata: dict = None):
        """Recibe la transcripción y lanza el ciclo LLM → tools."""
        if not texto.strip():
            return

        print(f"\n🧠 IA procesando: '{texto}'")
        self.historial.append({"role": "user", "content": texto})
        self._recortar_historial()

        try:
            respuesta = self._llamar_groq_con_reintento()
            self._interpretar_respuesta(respuesta)
        except Exception as e:
            print(f"❌ Error en ServicioIA: {e}")
            import traceback
            traceback.print_exc()
            # Fallback seguro: expresión neutral para no dejar la cara congelada
            try:
                self.gestor.aplicar_expresion("neutral")
            except Exception:
                pass

    # =========================================================================
    # GROQ — llamada con reintento tras BadRequestError
    # =========================================================================

    def _llamar_groq(self, temperatura: float = 0.7):
        mensajes = [{"role": "system", "content": self.SYSTEM_PROMPT}] + self.historial
        return self.cliente.chat.completions.create(
            model=self.modelo,
            messages=mensajes,
            tools=self._tools_activos,
            tool_choice="auto",
            max_tokens=1024,
            temperature=temperatura
        )

    def _llamar_groq_con_reintento(self):
        """
        Intenta llamar a Groq hasta 2 veces.
        Si el primer intento falla por tool_use_failed (valores fuera de schema),
        hace un segundo intento a temperatura 0 (más conservador) y sin historial
        reciente que pueda estar contaminado.
        """
        try:
            return self._llamar_groq(temperatura=0.7)

        except BadRequestError as e:
            error_body = str(e)
            if "tool_use_failed" in error_body or "tool call validation" in error_body:
                print(f"⚠️  Tool call inválida del LLM — reintentando con temperatura=0...")
                print(f"   Detalle: {error_body[:200]}")
                # Segundo intento: temperatura 0 genera respuestas más predecibles
                try:
                    return self._llamar_groq(temperatura=0.0)
                except BadRequestError as e2:
                    print(f"❌ Segundo intento también falló: {e2}")
                    raise
            else:
                raise

    # =========================================================================
    # INTERPRETACIÓN
    # =========================================================================

    def _interpretar_respuesta(self, respuesta):
        mensaje = respuesta.choices[0].message

        self.historial.append({
            "role": "assistant",
            "content": mensaje.content or ""
        })

        if mensaje.content:
            print(f"🤖 Zoé: {mensaje.content}")

        if mensaje.tool_calls:
            print(f"🔧 Ejecutando {len(mensaje.tool_calls)} tool(s)...")
            for tc in mensaje.tool_calls:
                self._ejecutar_tool(tc)

        elif mensaje.content:
            # El LLM no generó tool_calls formales pero puede haber escrito
            # la llamada como texto XML (<function=nombre>{args}</function>).
            # Intentamos rescatarla antes de caer a neutral.
            tools_rescatadas = self._rescatar_tools_de_texto(mensaje.content)
            if tools_rescatadas:
                print(f"🔧 Tools rescatadas del texto: {len(tools_rescatadas)}")
                for nombre, args in tools_rescatadas:
                    self._ejecutar_tool_directo(nombre, args)
            else:
                print("⚠️ LLM no usó tools — aplicando neutral")
                self.gestor.aplicar_expresion("neutral")
        else:
            print("⚠️ Respuesta vacía — aplicando neutral")
            self.gestor.aplicar_expresion("neutral")

    # ── Rescate de tool calls escritas como XML en el texto ──────────────────

    def _rescatar_tools_de_texto(self, texto: str) -> list[tuple[str, dict]]:
        """
        Detecta varios patrones donde el LLM intenta usar tools escribiéndolas como texto.
        Atrapa alucinaciones comunes de sintaxis XML.
        """
        import re
        import json
        
        resultados = []
        # Lista de nombres de tools válidos para evitar atrapar tags HTML normales
        herramientas_validas = [
            "expresion_cara", "mover_ojos", "mover_motor", 
            "mover_motores", "secuencia_expresiones", "parpadear",
            "respuesta_oral"
        ]

        # Patrones comunes que la IA suele inventar:
        patrones = [
            r"<function=(\w+)>(.*?)</function>", # Patrón 1: <function=nombre>{json}</function>
            r"<(\w+)>(.*?)</function>",          # Patrón 2: <nombre>{json}</function> (Tu error actual)
            r"<(\w+)>(.*?)</\1>"                 # Patrón 3: <nombre>{json}</nombre>
        ]

        for patron in patrones:
            for match in re.finditer(patron, texto, re.DOTALL):
                nombre = match.group(1)
                raw    = match.group(2).strip()
                
                # Verificamos que sea una herramienta real de Zoé
                if nombre in herramientas_validas:
                    try:
                        args = json.loads(raw)
                        # Evitar agregar duplicados si varios regex atrapan el mismo bloque
                        if (nombre, args) not in resultados:
                            resultados.append((nombre, args))
                    except json.JSONDecodeError:
                        print(f"⚠️ Rescate fallido: JSON inválido en la tool '{nombre}': {raw[:50]}")
                        
        return resultados
    
    def _ejecutar_tool(self, tool_call):
        """Ejecuta una tool call formal de la API."""
        nombre = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            print(f"❌ No se pudo parsear args de '{nombre}'")
            return
        self._ejecutar_tool_directo(nombre, args)

    def _ejecutar_tool_directo(self, nombre: str, args: dict):
        """
        Sanitiza los args y despacha la tool.
        La sanitización clampea valores numéricos al rango del schema
        ANTES de ejecutar — así nunca crashea por valores fuera de rango.
        """
        args = self._sanitizar_args(nombre, args)
        print(f"   🔧 {nombre}({args})")

        dispatch = {
            "expresion_cara":        self._tool_expresion_cara,
            "mover_ojos":            self._tool_mover_ojos,
            "mover_motor":           self._tool_mover_motor,
            "mover_motores":         self._tool_mover_motores,
            "secuencia_expresiones": self._tool_secuencia,
            "parpadear":             self._tool_parpadear,
            "respuesta_oral":        self._tool_respuesta_oral,
        }

        fn = dispatch.get(nombre)
        if fn:
            try:
                fn(args)
            except Exception as e:
                print(f"❌ Error ejecutando tool '{nombre}': {e}")
        else:
            print(f"⚠️ Tool desconocida: {nombre}")

    # ── Sanitización de args ─────────────────────────────────────────────────

    # Límites duros por campo — fuente única de verdad
    _LIMITES: dict[str, dict[str, tuple]] = {
        "parpadear": {
            "veces":       (1,   30),
            "velocidad_ms":(80,  10000),
        },
        "expresion_cara": {
            "intensidad":  (0.0, 1.0),
        },
        "mover_motor": {
            "angulo":      (0,   180),
        },
        "secuencia_expresiones": {
            # Se aplican por cada paso
            "duracion_ms": (100, 20000),
            "intensidad":  (0.0, 1.0),
        },
    }

    def _sanitizar_args(self, nombre: str, args: dict) -> dict:
        """
        Clampea valores numéricos al rango permitido.
        También corrige campos de tipo enum a valores válidos cuando es posible.
        Nunca lanza excepción — devuelve siempre un dict usable.
        """
        limites = self._LIMITES.get(nombre, {})

        def _clamp_num(key, val, lo, hi):
            if isinstance(val, (int, float)):
                clamped = max(lo, min(hi, val))
                if clamped != val:
                    print(f"   ⚙️  Sanitizado {nombre}.{key}: {val} → {clamped}")
                return clamped
            return val

        args = dict(args)  # copia para no mutar el original

        for campo, (lo, hi) in limites.items():
            if campo in args:
                args[campo] = _clamp_num(campo, args[campo], lo, hi)

        # Caso especial: secuencia_expresiones tiene límites dentro de cada paso
        if nombre == "secuencia_expresiones" and "pasos" in args:
            pasos_limpios = []
            for paso in args["pasos"]:
                paso = dict(paso)
                for campo in ("duracion_ms", "intensidad"):
                    lo, hi = self._LIMITES["secuencia_expresiones"][campo]
                    if campo in paso:
                        paso[campo] = _clamp_num(f"paso.{campo}", paso[campo], lo, hi)
                # Verificar que la emoción sea válida
                emociones_validas = set(["neutral"] + _EMOCIONES_DISPONIBLES)
                if paso.get("emocion") not in emociones_validas:
                    print(f"   ⚙️  Emoción inválida '{paso.get('emocion')}' → 'neutral'")
                    paso["emocion"] = "neutral"
                pasos_limpios.append(paso)
            args["pasos"] = pasos_limpios

        # Caso especial: mover_motores tiene angulo dentro de cada movimiento
        if nombre == "mover_motores" and "movimientos" in args:
            movs_limpios = []
            for mov in args["movimientos"]:
                mov = dict(mov)
                if "angulo" in mov:
                    mov["angulo"] = _clamp_num("movimiento.angulo", mov["angulo"], 0, 180)
                movs_limpios.append(mov)
            args["movimientos"] = movs_limpios

        return args

    # =========================================================================
    # IMPLEMENTACIÓN DE CADA TOOL
    # =========================================================================

    def _tool_expresion_cara(self, args: dict):
        self.gestor.aplicar_expresion(
            nombre=args["emocion"],
            intensidad=args.get("intensidad", 1.0)
        )

    def _tool_mover_ojos(self, args: dict):
        self.gestor.aplicar_mirada(
            horizontal=args["horizontal"],
            vertical=args["vertical"]
        )

    def _tool_mover_motor(self, args: dict):
        self.gestor.motor_por_nombre(
            nombre_motor=args["motor"],
            angulo=args["angulo"]
        )

    def _tool_mover_motores(self, args: dict):
        for mov in args["movimientos"]:
            self.gestor.motor_por_nombre(
                nombre_motor=mov["motor"],
                angulo=mov["angulo"]
            )

    def _tool_secuencia(self, args: dict):
        pasos   = args["pasos"]
        volver  = args.get("volver_a_neutral", True)

        def _run():
            for paso in pasos:
                self.gestor.aplicar_expresion(
                    nombre=paso["emocion"],
                    intensidad=paso.get("intensidad", 1.0)
                )
                time.sleep(paso["duracion_ms"] / 1000.0)
            if volver:
                self.gestor.aplicar_expresion("neutral", intensidad=0.6)

        threading.Thread(target=_run, daemon=True).start()
        print(f"   🎭 Secuencia: {[p['emocion'] for p in pasos]}")

    def _tool_parpadear(self, args: dict):
        veces     = args.get("veces", 1)
        velocidad = args.get("velocidad_ms", 200)
        ojo       = args.get("ojo", "ambos")

        motores: list[int] = []
        if ojo in ("ambos", "izquierdo"):
            motores.append(M_PARP_IZQ_SUP)
        if ojo in ("ambos", "derecho"):
            motores.append(M_PARP_DER_SUP)

        def _run():
            for _ in range(veces):
                for m in motores:
                    self.gestor.enviar_motor(m, 0)       # cerrar
                time.sleep(velocidad / 1000.0)
                for m in motores:
                    self.gestor.enviar_motor(m, 90)      # abrir
                time.sleep(velocidad / 1000.0)

        threading.Thread(target=_run, daemon=True).start()
        print(f"   👁️  Parpadeo: ojo={ojo}, veces={veces}, vel={velocidad}ms")

    # =========================================================================
    # HISTORIAL
    # =========================================================================

    def _recortar_historial(self):
        max_msgs = self.historial_max * 2
        if len(self.historial) > max_msgs:
            self.historial = self.historial[-max_msgs:]

    def limpiar_historial(self):
        self.historial.clear()
        print("🧹 Historial IA limpiado")

    # =========================================================================
    # TOOL: RESPUESTA ORAL
    # =========================================================================

    def _tool_respuesta_oral(self, args: dict):
        """
        Hace que Zoé hable en voz alta con el texto proporcionado.
        Los marcadores [EMOCION] en el texto se procesan en ServicioTTS
        para cambiar expresiones mientras habla.
        """
        texto = args.get("texto", "").strip()
        if not texto:
            return

        print(f"🗣️  Respuesta oral: '{texto[:80]}...'")

        if self.tts is None:
            print("⚠️  TTS no configurado — respuesta solo en consola")
            return

        # Cancelar cualquier habla anterior y comenzar la nueva en hilo daemon
        threading.Thread(
            target=self.tts.hablar,
            args=(texto,),
            daemon=True
        ).start()