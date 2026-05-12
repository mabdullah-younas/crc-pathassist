CAP_REPORT_SCHEMA = {
    "name": "generate_pathology_report",
    "description": "Generate a CAP-protocol-aligned synoptic pathology report for colorectal cancer from H&E patch images and clinical inputs.",
    "parameters": {
        "type": "object",
        "properties": {
            "tumour_type": {
                "type": "string",
                "description": "Histological type, e.g. 'Adenocarcinoma, NOS' or 'Mucinous adenocarcinoma'"
            },
            "differentiation_grade": {
                "type": "string",
                "enum": ["G1 - Well differentiated", "G2 - Moderately differentiated",
                         "G3 - Poorly differentiated", "G4 - Undifferentiated", "Cannot determine"],
                "description": "Histologic grade based on glandular architecture visible in H&E patches"
            },
            "pT_stage": {
                "type": "string",
                "enum": ["pT1","pT2","pT3","pT4a","pT4b","pTX","Cannot determine"],
                "description": "Pathologic T stage per AJCC 8th edition"
            },
            "pN_stage": {
                "type": "string",
                "enum": ["N0","N1","N1a","N1b","N1c","N2","N2a","N2b","NX","Cannot determine"]
            },
            "pM_stage": {
                "type": "string",
                "enum": ["M0","M1","M1a","M1b","MX","Cannot determine"]
            },
            "mmr_status": {
                "type": "string",
                "enum": ["Proficient MMR (pMMR)", "Deficient MMR (dMMR)", "Cannot determine"],
                "description": "Mismatch repair status. dMMR = MSI-High."
            },
            "mmr_proteins_lost": {
                "type": "array",
                "items": {"type": "string", "enum": ["MLH1","PMS2","MSH2","MSH6","None"]},
                "description": "Which MMR proteins show loss. Empty array if pMMR."
            },
            "kras_status": {
                "type": "string",
                "enum": ["Mutant","Wild-type","Not tested"]
            },
            "kras_codon": {
                "type": "string",
                "description": "Specific mutation if known, e.g. G12D. 'N/A' if wild-type."
            },
            "nras_status": {
                "type": "string",
                "enum": ["Mutant","Wild-type","Not tested"]
            },
            "braf_status": {
                "type": "string",
                "enum": ["Mutant","Wild-type","Not tested"]
            },
            "lymphovascular_invasion": {
                "type": "string",
                "enum": ["Present","Absent","Cannot determine"]
            },
            "perineural_invasion": {
                "type": "string",
                "enum": ["Present","Absent","Cannot determine"]
            },
            "tumour_budding": {
                "type": "string",
                "enum": ["Low (Bd1)","Intermediate (Bd2)","High (Bd3)","Cannot determine"]
            },
            "risk_tier": {
                "type": "string",
                "enum": ["Low","Intermediate","High","Very High"],
                "description": "Overall clinical risk stratification based on all findings"
            },
            "clinical_summary": {
                "type": "string",
                "description": "2-3 sentence narrative summary for the clinician. Mention key actionable findings."
            },
            "confidence": {
                "type": "string",
                "enum": ["High","Moderate","Low"],
                "description": "Model confidence in the overall report based on image quality and available inputs"
            }
        },
        "required": ["tumour_type","differentiation_grade","pT_stage","pN_stage",
                     "mmr_status","kras_status","nras_status","braf_status",
                     "risk_tier","clinical_summary","confidence"]
    }
}