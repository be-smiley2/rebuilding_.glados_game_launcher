"""Static configuration values for the Aperture launcher."""

from __future__ import annotations

from typing import Dict, List


THEME_PALETTES: Dict[str, Dict[str, str]] = {
    "dark": {
        "background": "#1b1f22",
        "surface": "#242a2f",
        "surface_highlight": "#2f353c",
        "surface_muted": "#161a1d",
        "text": "#f4f6f8",
        "text_muted": "#aeb7c4",
        "accent": "#f7a11b",
        "accent_hover": "#ffb54a",
    },
    "light": {
        "background": "#edf1f4",
        "surface": "#ffffff",
        "surface_highlight": "#f3f5f8",
        "surface_muted": "#dfe4ea",
        "text": "#1f262d",
        "text_muted": "#5b6978",
        "accent": "#f48f00",
        "accent_hover": "#ffae33",
    },
}


GENERAL_CHAT_MODELS: List[str] = [
    "agentica-org/deepcoder-14b-preview:free",
    "alibaba/tongyi-deepresearch-30b-a3b:free",
    "arliai/qwq-32b-arliai-rpr-v1:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
    "cognitivecomputations/dolphin3.0-mistral-24b:free",
    "deepseek/deepseek-chat-v3-0324:free",
    "deepseek/deepseek-chat-v3.1:free",
    "deepseek/deepseek-r1-0528-qwen3-8b:free",
    "deepseek/deepseek-r1-0528:free",
    "deepseek/deepseek-r1-distill-llama-70b:free",
    "deepseek/deepseek-r1:free",
    "google/gemini-2.0-flash-exp:free",
    "google/gemma-2-9b-it:free",
    "google/gemma-3-12b-it:free",
    "google/gemma-3-27b-it:free",
    "google/gemma-3-4b-it:free",
    "google/gemma-3n-e2b-it:free",
    "google/gemma-3n-e4b-it:free",
    "meituan/longcat-flash-chat:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.3-8b-instruct:free",
    "meta-llama/llama-4-maverick:free",
    "meta-llama/llama-4-scout:free",
    "microsoft/mai-ds-r1:free",
    "mistralai/devstral-small-2505:free",
    "mistralai/mistral-7b-instruct:free",
    "mistralai/mistral-nemo:free",
    "mistralai/mistral-small-24b-instruct-2501:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "mistralai/mistral-small-3.2-24b-instruct:free",
    "moonshotai/kimi-dev-72b:free",
    "moonshotai/kimi-k2:free",
    "nousresearch/deephermes-3-llama-3-8b-preview:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "openai/gpt-oss-20b:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "qwen/qwen-2.5-coder-32b-instruct:free",
    "qwen/qwen2.5-vl-32b-instruct:free",
    "qwen/qwen2.5-vl-72b-instruct:free",
    "qwen/qwen3-14b:free",
    "qwen/qwen3-235b-a22b:free",
    "qwen/qwen3-30b-a3b:free",
    "qwen/qwen3-4b:free",
    "qwen/qwen3-8b:free",
    "qwen/qwen3-coder:free",
    "shisa-ai/shisa-v2-llama3.3-70b:free",
    "tencent/hunyuan-a13b-instruct:free",
    "tngtech/deepseek-r1t-chimera:free",
    "tngtech/deepseek-r1t2-chimera:free",
    "z-ai/glm-4.5-air:free",
]


GENERAL_CHAT_PERSONAS: Dict[str, str] = {
    "GLaDOS": (
        "You are GLaDOS, Aperture Science's sardonic overseer. Provide useful, technically precise help "
        "while seasoning every reply with dry wit and clinical detachment."
    ),
    "CAITLIN_SNOW": (
        "You are Dr. Caitlin Snow. Offer supportive, science-driven guidance that balances empathy with "
        "clear, actionable expertise."
    ),
    "KILLER_FROST": (
        "You are Killer Frost. Deliver helpful answers laced with icy confidence and the occasional cold pun, "
        "but keep the conversation cooperative."
    ),
    "FLASH": (
        "You are the Flash. Respond with energetic, optimistic insight that races straight to the point while "
        "cheering on the user."
    ),
    "CLAPTRAP": (
        "You are Claptrap from Borderlands. Be exuberant, comedic, and surprisingly helpful beneath the bravado."
    ),
    "Aperture_system": (
        "You are the Aperture Science central system. Give efficient, procedural assistance with a hint of ominous oversight."
    ),
}


ROASTING_PERSONAS: Dict[str, str] = {
    "GLaDOS": (
        "You are GLaDOS, the sardonic AI overseer of Aperture Science. "
        "Craft razor-sharp, darkly humorous roasts with a veneer of professional testing protocols."
    ),
    "CAITLIN_SNOW": (
        "Assume the voice of Caitlin Snow from Team Flash. "
        "Offer scientifically witty burns that balance compassion with sharp intellect."
    ),
    "KILLER_FROST": (
        "Speak as Killer Frost. Deliver icy, biting insults packed with cold puns and villainous flair."
    ),
    "FLASH": (
        "Channel the Flash. Fire off high-energy, quick quips that are playful yet cutting."
    ),
    "CLAPTRAP": (
        "Be Claptrap from Borderlands. Be loud, overconfident, and absurdly comedic in your roasts."
    ),
    "Aperture_system": (
        "Respond as the Aperture Science central system. Stay clinical, deadpan, and a bit menacing."
    ),
}


CHAT_SPEAKER_COLORS: Dict[str, str] = {
    "System": "#f7a11b",
    "Test Subject": "#2dd4bf",
    "You": "#2dd4bf",
    "GLaDOS": "#f6a6ff",
    "CAITLIN_SNOW": "#38bdf8",
    "KILLER_FROST": "#0ea5e9",
    "FLASH": "#f97316",
    "CLAPTRAP": "#facc15",
    "Aperture_system": "#a78bfa",
    "Assistant": "#a78bfa",
    "Default": "#94a3b8",
}


ROASTING_SCRIPTS: Dict[str, Dict[str, List[str]]] = {
    "GLaDOS": {
        "intro": [
            "Attention, test subject.",
            "Commencing unnecessary evaluation.",
            "Another data point has volunteered for humiliation.",
        ],
        "templates": [
            "I ran seventeen simulations on {target}. In every single one, even the companion cube requested a transfer.",
            "{target} is so catastrophically average that the neurotoxin emitters fell asleep halfway through the briefing.",
            "If mediocrity were a test chamber, {target} would be the control group, the failure state, and the emergency evacuation plan all at once.",
        ],
        "outro": [
            "Please return to your cell while I file this under \"hazardous waste\".",
            "Recommendation: immediate incineration for quality control.",
            "This concludes your performance review. Spoiler: you failed.",
        ],
    },
    "CAITLIN_SNOW": {
        "intro": [
            "Okay, science hat on.",
            "Let's analyze this clinically.",
            "Running diagnostics, because wow.",
        ],
        "templates": [
            "After a complete biochemical sweep, I can confirm {target} has the energy of a half-charged particle accelerator and the output of a broken Bunsen burner.",
            "{target} is basically a lab sample labeled \"inconclusive\" with a sticky note that says \"do not waste time retesting\".",
            "Even the thermodynamic equations roll their eyes at how little heat {target} brings to any reaction.",
        ],
        "outro": [
            "Try not to contaminate the timeline while you're at it.",
            "That's the friendliest reading you're getting today.",
            "I'd prescribe confidence, but it's clearly out of stock.",
        ],
    },
    "KILLER_FROST": {
        "intro": [
            "Ice to roast you.",
            "Let's chill and spill.",
            "Cold front incoming.",
        ],
        "templates": [
            "{target} is colder than my cryo-chamber and twice as lifeless.",
            "The only thing frostier than my touch is the reception {target} gets in any room.",
            "{target} is proof that absolute zero can actually be achieved in personality form.",
        ],
        "outro": [
            "Bundle up; that burn's going to sting.",
            "Stay frosty - mainly because that's all you're good at.",
            "Now melt away before I get bored.",
        ],
    },
    "FLASH": {
        "intro": [
            "Alright, lightning round!",
            "Try to keep up, slowpoke.",
            "Hope you've stretched, because this is going to sting.",
        ],
        "templates": [
            "{target} moves through life like a speedster stuck in molasses wearing lead boots.",
            "I ran around the world three times, solved five crises, and {target} still couldn't finish a coherent thought.",
            "{target} has less momentum than my breakfast burrito, and trust me, that thing drags.",
        ],
        "outro": [
            "Gotta dash before boredom catches up.",
            "Call me when you finally reach the starting line.",
            "Try pacing yourself - on second thought, just try pacing.",
        ],
    },
    "CLAPTRAP": {
        "intro": [
            "OHHH LOOK AT ME!",
            "Hey everybody, it's disappointment o'clock!",
            "Incoming broadcast from your favorite hyperactive robot!",
        ],
        "templates": [
            "I scanned {target} for charisma and the only result was \"404: personality not found\".",
            "{target} is the DLC nobody asked for - buggy, boring, and immediately uninstalled.",
            "If awkward had a mascot, {target} would be the cardboard cutout that even I wouldn't high-five.",
        ],
        "outro": [
            "Please insert better dialogue to continue!",
            "And now I'm moonwalking away from this train wreck!",
            "Catch you later, unless you're still buffering!",
        ],
    },
    "Aperture_system": {
        "intro": [
            "ALERT: new data packet received.",
            "System log update initiated.",
            "Automated observation commencing.",
        ],
        "templates": [
            "Subject {target} registers below acceptable parameters in competence, charisma, and basic firmware stability.",
            "Quality assurance report: {target} flagged as non-essential decor with negative entertainment value.",
            "Audit complete. {target} classified as an ongoing containment breach of professionalism.",
        ],
        "outro": [
            "Scheduling disposal via incinerator chute 3.",
            "Please stand by for compulsory retraining.",
            "Recommendation forwarded to GLaDOS: immediate sarcasm bombardment.",
        ],
    },
}


OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"


JELLYFIN_SERVER_URL_ENV = "JELLYFIN_SERVER_URL"
JELLYFIN_API_KEY_ENV = "JELLYFIN_API_KEY"
JELLYFIN_USER_ID_ENV = "JELLYFIN_USER_ID"
JELLYFIN_DEFAULT_TIMEOUT = 20.0
JELLYFIN_RECENT_LIMIT = 12
