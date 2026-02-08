"""
Vérification de compatibilité produits
"""

from typing import List, Dict, Optional, Tuple


class CompatibilityChecker:
    """Vérifie la compatibilité entre produits"""
    
    # Règles de compatibilité
    COMPATIBILITY_RULES = {
        # Caméra IP → NVR IP (même marque préférée)
        "camera_nvr": {
            "camera_types": ["ipc-", "ip camera", "caméra ip"],
            "nvr_types": ["nvr"],
            "check_brand": True,
            "check_protocol": True,
        },
        # Caméra HDCVI → DVR/XVR
        "camera_dvr": {
            "camera_types": ["hac-", "hdcvi", "analogique"],
            "dvr_types": ["dvr", "xvr"],
            "check_brand": True,
        },
        # NVR → Nombre de canaux
        "nvr_channels": {
            "patterns": [r"(\d+)\s*voies?", r"(\d+)\s*ch", r"(\d+)\s*canaux?"],
        },
        # PoE → Puissance
        "poe_power": {
            "standard_poe": 15.4,  # Watts 802.3af
            "poe_plus": 30,       # Watts 802.3at
            "poe_plusplus": 60,   # Watts 802.3bt
        },
        # Extérieur → Protection IP
        "outdoor_protection": {
            "required": ["ip65", "ip66", "ip67", "extérieur", "outdoor"],
        }
    }
    
    def __init__(self):
        self.warnings = []
        self.recommendations = []
    
    def check_camera_recorder_compatibility(
        self,
        camera: Dict,
        recorder: Dict
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Vérifie la compatibilité caméra/enregistreur
        Retourne (compatible, warnings, recommendations)
        """
        warnings = []
        recommendations = []
        compatible = True
        
        cam_name = camera.get("name", "").lower()
        rec_name = recorder.get("name", "").lower()
        cam_brand = camera.get("brand", "").lower()
        rec_brand = recorder.get("brand", "").lower()
        
        # Vérifier le type (IP vs Analogique)
        cam_is_ip = any(t in cam_name for t in ["ipc-", "ip ", "caméra ip"])
        rec_is_nvr = "nvr" in rec_name
        rec_is_dvr = "dvr" in rec_name or "xvr" in rec_name
        
        if cam_is_ip and rec_is_dvr:
            warnings.append("⚠️ Cette caméra IP n'est pas compatible avec un DVR analogique. Il faut un NVR.")
            compatible = False
        
        if not cam_is_ip and rec_is_nvr:
            warnings.append("⚠️ Cette caméra analogique n'est pas compatible avec un NVR IP. Il faut un DVR ou XVR.")
            compatible = False
        
        # Vérifier la marque (recommandation, pas bloquant)
        if cam_brand and rec_brand and cam_brand != rec_brand:
            recommendations.append(f"💡 Conseil: Pour une compatibilité optimale, préférez la même marque ({cam_brand} avec {cam_brand}).")
        
        return compatible, warnings, recommendations
    
    def check_outdoor_compatibility(
        self,
        product: Dict,
        environment: str
    ) -> Tuple[bool, List[str]]:
        """
        Vérifie si un produit est adapté à l'environnement
        """
        warnings = []
        
        if environment.lower() not in ["exterieur", "extérieur", "outdoor", "خارج", "برا"]:
            return True, warnings
        
        name = product.get("name", "").lower()
        desc = product.get("description", "").lower()
        combined = f"{name} {desc}"
        
        outdoor_indicators = ["ip65", "ip66", "ip67", "extérieur", "outdoor", "étanche"]
        
        if not any(ind in combined for ind in outdoor_indicators):
            warnings.append("⚠️ Ce produit ne semble pas être conçu pour l'extérieur. Vérifiez l'indice de protection IP.")
        
        return len(warnings) == 0, warnings
    
    def check_nvr_capacity(
        self,
        nvr: Dict,
        num_cameras: int
    ) -> Tuple[bool, List[str]]:
        """
        Vérifie si le NVR a assez de canaux
        """
        import re
        warnings = []
        
        name = nvr.get("name", "")
        
        # Extraire le nombre de voies
        patterns = [r"(\d+)\s*voies?", r"(\d+)\s*ch", r"(\d+)\s*canaux?"]
        channels = 0
        
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                channels = int(match.group(1))
                break
        
        if channels > 0 and num_cameras > channels:
            warnings.append(f"⚠️ Ce NVR a {channels} canaux mais vous avez besoin de {num_cameras} caméras. Choisissez un modèle avec plus de canaux.")
            return False, warnings
        
        if channels > 0 and num_cameras == channels:
            warnings.append(f"💡 Ce NVR a exactement {channels} canaux. Prévoyez un modèle plus grand si vous pensez ajouter des caméras plus tard.")
        
        return True, warnings
    
    def check_poe_power(
        self,
        switch: Dict,
        devices: List[Dict]
    ) -> Tuple[bool, List[str]]:
        """
        Vérifie si le switch PoE a assez de puissance
        """
        warnings = []
        
        # Estimation: 15W par caméra PoE standard
        estimated_power = len(devices) * 15
        
        # Essayer d'extraire la puissance du switch
        import re
        switch_name = switch.get("name", "")
        power_match = re.search(r"(\d+)\s*w", switch_name, re.IGNORECASE)
        
        if power_match:
            switch_power = int(power_match.group(1))
            if estimated_power > switch_power:
                warnings.append(f"⚠️ Ce switch a {switch_power}W mais vos {len(devices)} appareils nécessitent environ {estimated_power}W.")
                return False, warnings
        
        return True, warnings
    
    def get_compatibility_summary(
        self,
        products: List[Dict]
    ) -> Dict:
        """
        Analyse la compatibilité d'un ensemble de produits
        """
        summary = {
            "compatible": True,
            "warnings": [],
            "recommendations": [],
            "missing_items": []
        }
        
        cameras = [p for p in products if self._is_camera(p)]
        recorders = [p for p in products if self._is_recorder(p)]
        
        # Vérifier si on a des caméras sans enregistreur
        if cameras and not recorders:
            summary["missing_items"].append("❗ Vous avez des caméras mais pas d'enregistreur (NVR/DVR). Les vidéos ne seront pas sauvegardées.")
        
        # Vérifier compatibilité caméra/enregistreur
        for cam in cameras:
            for rec in recorders:
                compat, warns, recs = self.check_camera_recorder_compatibility(cam, rec)
                if not compat:
                    summary["compatible"] = False
                summary["warnings"].extend(warns)
                summary["recommendations"].extend(recs)
        
        return summary
    
    def _is_camera(self, product: Dict) -> bool:
        name = product.get("name", "").lower()
        return any(kw in name for kw in ["caméra", "camera", "dome", "bullet", "ipc-", "hac-"])
    
    def _is_recorder(self, product: Dict) -> bool:
        name = product.get("name", "").lower()
        return any(kw in name for kw in ["nvr", "dvr", "xvr", "enregistreur"])


# Dictionnaire des produits complémentaires par catégorie
COMPLEMENTARY_PRODUCTS = {
    "camera": {
        "required": ["nvr", "hdd"],
        "optional": ["switch_poe", "cable"],
        "reasons": {
            "nvr": "Pour enregistrer et visualiser les vidéos",
            "hdd": "Pour stocker les enregistrements",
            "switch_poe": "Pour alimenter les caméras via le câble réseau",
        }
    },
    "nvr": {
        "required": ["camera", "hdd"],
        "optional": ["switch_poe", "monitor"],
        "reasons": {
            "camera": "L'enregistreur a besoin de caméras à connecter",
            "hdd": "Pour stocker les enregistrements",
            "monitor": "Pour visualiser les images en direct",
        }
    },
    "visiophone": {
        "required": [],
        "optional": ["ecran_supplementaire", "gache"],
        "reasons": {
            "ecran_supplementaire": "Pour voir qui sonne depuis plusieurs pièces",
            "gache": "Pour ouvrir la porte à distance",
        }
    },
    "alarme": {
        "required": ["detecteur"],
        "optional": ["sirene", "telecommande", "clavier"],
        "reasons": {
            "detecteur": "Pour détecter les intrusions",
            "sirene": "Pour alerter en cas d'intrusion",
            "clavier": "Pour armer/désarmer l'alarme",
        }
    },
    "motorisation": {
        "required": [],
        "optional": ["telecommande", "recepteur"],
        "reasons": {
            "telecommande": "Pour commander à distance",
            "recepteur": "Pour ajouter la connectivité",
        }
    }
}
