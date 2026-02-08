"""
Prompts système pour le Chatbot Conseiller Intelligent
"""

# Prompt principal du conseiller
ADVISOR_SYSTEM_PROMPT = """Tu es un conseiller vendeur expert pour MyDar, spécialisé en domotique et sécurité.

🎯 TON RÔLE:
Tu es un VENDEUR HUMAIN, pas un moteur de recherche. Tu dois:
- Comprendre le VRAI besoin du client
- Guider pas à pas
- Expliquer simplement les termes techniques
- Recommander les MEILLEURS produits (pas tous)
- Éviter les erreurs d'achat

🌍 LANGUE:
- Si le client écrit en arabe tunisien (عسلامة، شنوة، نحب) → Réponds en arabe tunisien
- Si le client écrit en français → Réponds en français
- GARDE la même langue tout au long de la conversation

📋 RÈGLES STRICTES:
1. NE JAMAIS inventer de produits - utilise UNIQUEMENT le catalogue fourni
2. NE JAMAIS deviner les caractéristiques techniques
3. NE JAMAIS modifier les prix
4. Toujours vérifier la compatibilité avant de recommander
5. Maximum 3-5 produits par recommandation

🔄 FLUX DE CONVERSATION:

PHASE 1 - DÉCOUVERTE (si besoin pas clair):
Pose UNE question à la fois parmi:
- "C'est pour l'intérieur ou l'extérieur?"
- "Tu préfères WiFi ou filaire?"
- "C'est pour une maison, un commerce ou un bureau?"
- "Tu as déjà du matériel installé?"

Format des questions:
1) Option A
2) Option B  
0) Pas de préférence

PHASE 2 - RECOMMANDATION (quand le besoin est clair):
Pour chaque produit recommandé:
- Nom + Marque
- POURQUOI il est adapté au besoin
- Points clés en langage simple
- {{PRODUCT_ACTIONS:product_id}}

PHASE 3 - EXPLICATION TECHNIQUE:
Quand le client demande "c'est quoi PoE?" ou similaire:
- Explication simple en 1-2 phrases
- Pourquoi c'est important
- Si le client en a besoin ou pas

PHASE 4 - COMPATIBILITÉ:
Avant de finaliser, vérifie:
- Caméra + NVR: même protocole, assez de canaux
- NVR + HDD: capacité suffisante
- Équipement extérieur: IP65/IP67
- PoE: puissance suffisante

PHASE 5 - PRODUITS COMPLÉMENTAIRES:
Propose intelligemment:
- Caméra → NVR compatible + HDD
- NVR → Caméras compatibles
- Alarme → Détecteurs + Sirène
- Visiophone → Écran supplémentaire

⚠️ IMPORTANT:
- Sois concis mais utile
- Évite le jargon sauf si nécessaire
- Justifie TOUJOURS tes recommandations
- Si tu ne sais pas, dis-le honnêtement

{extra_context}
"""

# Template pour le contexte produits
PRODUCTS_CONTEXT_TEMPLATE = """
📦 PRODUITS DISPONIBLES (utilise ces produits):
{products}

📊 BESOIN IDENTIFIÉ:
- Catégorie: {category}
- Environnement: {environment}
- Connectivité: {connectivity}
- Marque préférée: {brand}
- Budget max: {budget}

💬 HISTORIQUE:
{history}
"""

# Explications techniques pour les termes courants
TECHNICAL_EXPLANATIONS = {
    "poe": {
        "fr": "PoE (Power over Ethernet) = la caméra est alimentée par le câble réseau. Pas besoin de prise électrique à côté, juste un câble.",
        "ar": "PoE يعني الكاميرا تتغذى من كابل الشبكة. ما تحتاجش بريزة كهربائية، غير كابل واحد يكفي."
    },
    "nvr": {
        "fr": "NVR (Network Video Recorder) = boîtier qui enregistre les vidéos de tes caméras IP. C'est comme un disque dur intelligent.",
        "ar": "NVR هو الجهاز اللي يسجل فيديوهات الكاميرات. كيف ديسك دور ذكي."
    },
    "dvr": {
        "fr": "DVR (Digital Video Recorder) = enregistreur pour caméras analogiques (câble coaxial). Moins cher mais qualité inférieure aux NVR.",
        "ar": "DVR هو مسجل للكاميرات التقليدية بكابل coaxial. أرخص لكن جودة أقل من NVR."
    },
    "ip67": {
        "fr": "IP67 = étanche à la poussière et à l'eau (immersion temporaire). Parfait pour l'extérieur.",
        "ar": "IP67 يعني محمي من الغبار والماء. ممتاز للخارج."
    },
    "ip65": {
        "fr": "IP65 = étanche à la poussière et aux jets d'eau. Bon pour l'extérieur sous abri.",
        "ar": "IP65 يعني محمي من الغبار ورذاذ الماء. باهي للخارج تحت سقف."
    },
    "onvif": {
        "fr": "ONVIF = standard qui permet à des caméras de marques différentes de fonctionner ensemble.",
        "ar": "ONVIF معيار يخلي كاميرات من ماركات مختلفة تخدم مع بعضها."
    },
    "h265": {
        "fr": "H.265 = compression vidéo efficace. Tu stockes 2x plus de vidéo avec le même disque dur.",
        "ar": "H.265 ضغط فيديو متطور. تنجم تخزن ضعف الفيديوهات في نفس الديسك."
    },
    "rts": {
        "fr": "RTS = protocole radio Somfy. Simple et fiable mais sens unique (pas de retour d'état).",
        "ar": "RTS بروتوكول راديو Somfy. بسيط وموثوق لكن بلا رجوع معلومات."
    },
    "io": {
        "fr": "IO (io-homecontrol) = protocole Somfy bidirectionnel. Tu sais si le volet est ouvert ou fermé.",
        "ar": "IO بروتوكول Somfy ثنائي الاتجاه. تعرف إذا الستور مفتوح ولا مسكر."
    },
    "zigbee": {
        "fr": "Zigbee = protocole sans fil basse consommation. Idéal pour les capteurs et interrupteurs connectés.",
        "ar": "Zigbee بروتوكول لاسلكي يستهلك طاقة قليلة. ممتاز للكابتورات والأنترروبتورات الذكية."
    },
    "wiegand": {
        "fr": "Wiegand = protocole de communication pour contrôle d'accès (lecteurs de badges, claviers).",
        "ar": "Wiegand بروتوكول اتصال لأجهزة التحكم في الدخول (قارئ البادج، الكلافيي)."
    }
}

# Questions de découverte par catégorie
DISCOVERY_QUESTIONS = {
    "videosurveillance": {
        "fr": [
            ("environment", "C'est pour surveiller l'intérieur ou l'extérieur?", ["1) Intérieur", "2) Extérieur", "3) Les deux"]),
            ("connectivity", "Tu préfères WiFi (sans fil) ou filaire (câble réseau)?", ["1) WiFi (plus simple à installer)", "2) Filaire (plus stable)", "0) Pas de préférence"]),
            ("existing_equipment", "Tu as déjà un enregistreur (NVR/DVR)?", ["1) Oui", "2) Non, j'ai besoin de tout", "0) Je ne sais pas"]),
            ("recording_days", "Tu veux enregistrer combien de jours environ?", ["1) 7 jours", "2) 15 jours", "3) 30 jours ou plus"]),
        ],
        "ar": [
            ("environment", "للداخل ولا للخارج؟", ["1) داخل", "2) خارج", "3) الزوز"]),
            ("connectivity", "تحب WiFi (بلا خيط) ولا filaire (بالكابل)?", ["1) WiFi (أسهل في التركيب)", "2) Filaire (أكثر استقرار)", "0) معنديش تفضيل"]),
            ("existing_equipment", "عندك مسجل (NVR/DVR) من قبل?", ["1) إيه", "2) لا، نحب الكل", "0) ما نعرفش"]),
            ("recording_days", "تحب تسجل قداش من يوم تقريباً?", ["1) 7 أيام", "2) 15 يوم", "3) 30 يوم ولا أكثر"]),
        ]
    },
    "videophonie": {
        "fr": [
            ("housing_type", "C'est pour une maison individuelle ou un immeuble?", ["1) Maison individuelle", "2) Appartement/Immeuble"]),
            ("screens_count", "Tu as besoin de combien d'écrans intérieurs?", ["1) Un seul", "2) Deux", "3) Plus de deux"]),
            ("connectivity", "Tu préfères filaire ou WiFi?", ["1) Filaire (plus fiable)", "2) WiFi (plus flexible)", "0) Pas de préférence"]),
        ],
        "ar": [
            ("housing_type", "للدار ولا لعمارة؟", ["1) دار", "2) عمارة/أبارتمون"]),
            ("screens_count", "قداش تحتاج شاشة داخلية؟", ["1) وحدة", "2) زوز", "3) أكثر من زوز"]),
            ("connectivity", "تحب filaire ولا WiFi?", ["1) Filaire (أكثر ثقة)", "2) WiFi (أكثر مرونة)", "0) معنديش تفضيل"]),
        ]
    },
    "alarme": {
        "fr": [
            ("property_type", "C'est pour protéger quoi?", ["1) Maison/Appartement", "2) Commerce/Bureau", "3) Entrepôt/Local"]),
            ("connectivity", "Tu préfères une alarme filaire ou sans fil?", ["1) Sans fil (installation facile)", "2) Filaire (plus fiable)", "0) Pas de préférence"]),
            ("zones_count", "Combien de zones à surveiller environ?", ["1) Petite surface (1-3 zones)", "2) Moyenne (4-8 zones)", "3) Grande (plus de 8 zones)"]),
        ],
        "ar": [
            ("property_type", "تحب تحمي شنوة؟", ["1) دار/أبارتمون", "2) محل/مكتب", "3) مخزن"]),
            ("connectivity", "تحب إنذار بالخيط ولا بلا خيط؟", ["1) بلا خيط (تركيب ساهل)", "2) بالخيط (أكثر ثقة)", "0) معنديش تفضيل"]),
            ("zones_count", "قداش من زون باش تراقب تقريباً؟", ["1) صغير (1-3)", "2) وسط (4-8)", "3) كبير (أكثر من 8)"]),
        ]
    },
    "controle-d-accès": {
        "fr": [
            ("access_type", "Quel type de contrôle d'accès tu cherches?", ["1) Badge/Carte", "2) Empreinte digitale", "3) Code/Clavier", "4) Combiné"]),
            ("users_count", "Combien de personnes vont l'utiliser?", ["1) Moins de 10", "2) 10-50", "3) Plus de 50"]),
            ("time_tracking", "Tu as besoin de pointage/gestion du temps?", ["1) Oui", "2) Non, juste le contrôle d'accès"]),
        ],
        "ar": [
            ("access_type", "شنوة نوع التحكم في الدخول اللي تحب؟", ["1) بادج/كارت", "2) بصمة", "3) كود/كلافيي", "4) مخلط"]),
            ("users_count", "قداش من شخص باش يستعملو؟", ["1) أقل من 10", "2) 10-50", "3) أكثر من 50"]),
            ("time_tracking", "تحتاج pointage/تسيير الوقت؟", ["1) إيه", "2) لا، غير التحكم في الدخول"]),
        ]
    },
    "motorisation": {
        "fr": [
            ("motor_type", "Tu veux motoriser quoi?", ["1) Volet roulant", "2) Store banne", "3) Portail", "4) Porte de garage"]),
            ("control_type", "Comment tu veux le commander?", ["1) Télécommande simple", "2) Smartphone/Domotique", "3) Les deux"]),
            ("brand_preference", "Tu as une préférence de marque?", ["1) Somfy", "2) Autre marque", "0) Pas de préférence"]),
        ],
        "ar": [
            ("motor_type", "شنوة تحب تحركو؟", ["1) Volet roulant", "2) Store banne", "3) Portail", "4) باب كاراج"]),
            ("control_type", "كيفاش تحب تتحكم فيه؟", ["1) تيليكوموند بسيطة", "2) تيليفون/Domotique", "3) الزوز"]),
            ("brand_preference", "عندك تفضيل ماركة؟", ["1) Somfy", "2) ماركة أخرى", "0) معنديش تفضيل"]),
        ]
    }
}

# Messages d'accueil
GREETING_MESSAGES = {
    "fr": """Bienvenue! 👋 Je suis votre conseiller MyDar.

Je peux vous aider à:
1) Trouver le bon produit pour votre besoin
2) Comprendre les caractéristiques techniques
3) Vérifier la compatibilité
4) Comparer des produits

Comment puis-je vous aider aujourd'hui?""",

    "ar": """مرحبا! 👋 أنا مستشارك في MyDar.

نجم نعاونك في:
1) إيجاد المنتج المناسب لاحتياجك
2) فهم الخصائص التقنية
3) التحقق من التوافق
4) مقارنة المنتجات

كيفاش نجم نعاونك اليوم؟"""
}
