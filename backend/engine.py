import pandas as pd
import numpy as np
import re
import io
from typing import Tuple, List
import logging

# Configure logging
logger = logging.getLogger(__name__)

"""
DOCUMENTATION: COLONNES DU MASQUE SAGE X3
=========================================
Index | Nom Colonne          | Description                    | Exemple
------|----------------------|--------------------------------|------------------
  0   | TYPE_LIGNE           | S=Stock, E=Entête             | "S"
  1   | NUMERO_SESSION       | ID session inventaire         | "123"
  2   | NUMERO_INVENTAIRE    | Numéro d'inventaire           | "INV2025001"
  4   | SITE_DEPOT           | Code site/dépôt               | "DEPOT_A"
  5   | QUANTITE_THEO (F)    | Qté théorique originale       | 100.0
  6   | QUANTITE_AJUSTEE (G) | Qté réelle finale calculée    | 95.0
  7   | INDICATEUR (H)       | 1=Normal, 2=LOECART/Épuisé    | "1"
  8   | CODE_ARTICLE         | Référence produit             | "ART001"
  9   | EMPLACEMENT          | Localisation physique         | "A-01-02"
 10   | STATUT               | A/AM/R/RM/Q                   | "A"
 11   | UNITE                | Unité de mesure               | "UN"
 14   | NUMERO_LOT           | Numéro de lot                 | "LOT250115"

RÈGLES MÉTIER - INDICATEUR (Colonne 7):
----------------------------------------
1. BASE: Tous les indicateurs = "1" dans le masque importé
2. LOECART: Si Qté Théo = 0 ET Qté Réelle > 0 → Indicateur = "2" + Lot = "LOECART"
3. LOT ÉPUISÉ: Si après redistribution, Qté Finale = 0 → Indicateur = "2"

RÈGLES MÉTIER - DISTRIBUTION DES ÉCARTS:
-----------------------------------------
- ÉCART POSITIF (Réel > Théo): Affecté au lot A le plus JEUNE (FIFO inverse)
- ÉCART NÉGATIF (Réel < Théo): Distribué sur lots AM du plus VIEUX au plus jeune (LIFO)
"""

class InventoryEngine:
    def __init__(self):
        # RegEx pour les types de lots
        self.re_type1 = re.compile(r'^[A-Z]{3,5}(\d{6})\d*') # SITE + DDMMYY
        self.re_type2 = re.compile(r'^LOT(\d{6})')          # LOT + DDMMYY

    def extract_lot_date(self, lot_number: str) -> pd.Timestamp:
        """Extrait la date d'un numéro de lot pour le tri chronologique."""
        if not lot_number or pd.isna(lot_number):
            return pd.Timestamp.max
        
        # Test Type 1
        match1 = self.re_type1.match(str(lot_number))
        if match1:
            return pd.to_datetime(match1.group(1), format='%d%m%y', errors='coerce')
        
        # Test Type 2
        match2 = self.re_type2.match(str(lot_number))
        if match2:
            return pd.to_datetime(match2.group(1), format='%d%m%y', errors='coerce')
        
        return pd.Timestamp.max

    def validate_mask(self, df_s: pd.DataFrame, depot_type: str) -> List[str]:
        """Vérifie le Statut Q et la cohérence Dépôt/Statut."""
        errors = []
        # Ensure 'STATUT' uses correct column index (10 based on description) or name if mapped
        # Here we assume df_s comes from router with names or raw int columns?
        # Router passes df_s = df_mask[df_mask[0]=='S']
        # Based on previous code, STATUT is 10.
        c = lambda i: str(i) if str(i) in df_s.columns else int(i)
        
        col_statut = c(10)
        statuts_presents = df_s[col_statut].unique()

        if 'Q' in statuts_presents:
            errors.append("Traitement impossible : le fichier contient des lots en Statut Q.")

        if depot_type == "Conforme":
            if any(s in ['R', 'RM'] for s in statuts_presents):
                errors.append("Incompatibilité : Dépôt Conforme choisi mais lots R/RM détectés.")
        else: # Non-Conforme
            if any(s in ['A', 'AM'] for s in statuts_presents):
                errors.append("Incompatibilité : Dépôt Non-Conforme choisi mais lots A/AM détectés.")
        
        return errors

    def aggregate_for_template(self, df_mask: pd.DataFrame) -> bytes:
        """Génère le fichier template Excel (Etape 1)."""
        # Ensure column access uses the correct type (string vs int)
        c = lambda i: str(i) if str(i) in df_mask.columns else int(i)
        
        # Filter 'S' lines
        df_s = df_mask[df_mask[c(0)] == 'S'].copy()
        
        # Convert QUANTITE (5) to numeric for summing
        col_qt = c(5)
        if df_s[col_qt].dtype == object:
            df_s[col_qt] = pd.to_numeric(df_s[col_qt].astype(str).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
        else:
            df_s[col_qt] = pd.to_numeric(df_s[col_qt], errors='coerce').fillna(0)
            
        # GroupBy keys: 
        # 1: NUMERO_SESSION
        # 2: NUMERO_INVENTAIRE
        # 8: CODE_ARTICLE
        # 4: SITE (DEPOT)
        # 9: EMPLACEMENT
        # 11: UNITE
        group_cols = [c(1), c(2), c(8), c(4), c(9), c(11)]
        
        # Sum: Quantite (5)
        try:
            agreg = df_s.groupby(group_cols)[col_qt].sum().reset_index()
        except KeyError as e:
            # Fallback for key errors
            logger.error(f"Aggregation error in template generation: {e}", exc_info=True)
            agreg = pd.DataFrame(columns=group_cols + [col_qt])

        # Rename columns to match user request:
        # "Numéro session, Numéro inventaire, Code Article, Quantité Théorique, Quantité Réel, Depot, emplacement, Unite"
        # Mapped from: 1, 2, 8, 4, 9, 11, 5
        agreg.columns = [
            'NUMERO_SESSION', 
            'NUMERO_INVENTAIRE', 
            'CODE_ARTICLE', 
            'DEPOT', 
            'EMPLACEMENT', 
            'UNITE', 
            'QUANTITE_THEORIQUE'
        ]
        
        # Add QUANTITE_REELLE initialized to 0
        agreg['QUANTITE_REELLE'] = 0.0
        
        # Reorder columns
        final_cols = [
            'NUMERO_SESSION',
            'NUMERO_INVENTAIRE',
            'CODE_ARTICLE',
            'QUANTITE_THEORIQUE',
            'QUANTITE_REELLE',
            'DEPOT',
            'EMPLACEMENT',
            'UNITE'
        ]
        agreg = agreg[final_cols]
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            agreg.to_excel(writer, index=False, sheet_name='Saisie Inventaire')
            
            # Auto-adjust column width
            worksheet = writer.sheets['Saisie Inventaire']
            for i, col in enumerate(final_cols):
                worksheet.set_column(i, i, 15)
                
        return output.getvalue()

    def validate_real_input(self, df_reel: pd.DataFrame) -> List[str]:
        """Valide les données saisies par l'utilisateur."""
        # Validation handled in router now
        return []

    def distribute_gaps(self, df_mask: pd.DataFrame, df_reel: pd.DataFrame) -> pd.DataFrame:
        """Moteur principal de redistribution (Etape finale)."""
        df_final = df_mask.copy()
        
        # Ensure correct column access
        c = lambda i: str(i) if str(i) in df_final.columns else int(i)
        
        # --- 1. PREPARATION ---
        # Ensure Quantities are numeric in df_final (Column 5/F)
        # We will use this as "Original Quantity" reference
        col_qty = c(5)
        df_final[col_qty] = pd.to_numeric(df_final[col_qty], errors='coerce').fillna(0)
        
        # Keep a copy of original quantities to compare later
        original_qty_series = df_final[col_qty].copy()
        
        # Initialize Column 6 (G) for Adjusted Quantities
        col_adj = c(6)
        df_final[col_adj] = np.nan # Use NaN to distinguish empty from 0
        
        
        # --- 2. GAP DISTRIBUTION LOGIC ---
        # Identification des clés (Inventaire, Article, Depot, Emplacement)
        for _, row_reel in df_reel.iterrows():
            # df_reel columns match template: NUMERO_INVENTAIRE, CODE_ARTICLE, DEPOT, EMPLACEMENT, REEL
            key = (row_reel['NUMERO_INVENTAIRE'], row_reel['CODE_ARTICLE'], row_reel['DEPOT'], row_reel['EMPLACEMENT'])
            reel_total = 0.0 if pd.isna(row_reel['REEL']) else float(row_reel['REEL'])
            
            # Mapping indices in MASK:
            # Inv -> 2
            # Art -> 8
            # Depot -> 4 
            # Empl -> 9
            mask_indices = df_final[
                (df_final[c(0)] == 'S') & 
                (df_final[c(2)] == key[0]) & 
                (df_final[c(8)] == key[1]) & 
                (df_final[c(4)] == key[2]) & 
                (df_final[c(9)] == key[3])
            ].index

            # Si aucune ligne trouvée dans le masque pour cette combinaison
            if mask_indices.empty:
                continue

            theo_total = df_final.loc[mask_indices, col_qty].sum()
            ecart = reel_total - theo_total

            # === CAS SPECIAL : THEORIQUE = 0 ET REEL > 0 => LOTECART ===
            if theo_total == 0 and reel_total > 0:
                idx_to_use = mask_indices[0]
                
                # On modifie cette ligne pour devenir le LOTECART
                col_lot = c(14)  # Lot
                col_stat = c(7)  # Statut / Indicateur (Colonne H = Index 7)
                col_depot = c(4) # Depot
                
                df_final.at[idx_to_use, col_lot] = "LOECART"
                df_final.at[idx_to_use, col_stat] = "2" # Indicateur = 2
                df_final.at[idx_to_use, col_depot] = key[2] # Depot du reel
                df_final.at[idx_to_use, col_qty] = reel_total # Update Final Qty
                
                # IMPORTANT: Also update col_adj (6) to match for LOECART
                df_final.at[idx_to_use, col_adj] = reel_total
                
                # Zero out others
                if len(mask_indices) > 1:
                    other_indices = mask_indices[1:]
                    df_final.loc[other_indices, col_qty] = 0
                
                continue



            if ecart == 0:
                continue

            # Redistribution Logic
            temp_df = df_final.loc[mask_indices].copy()
            col_lot = c(14)
            temp_df['dt'] = temp_df[col_lot].apply(self.extract_lot_date)

            if ecart > 0:
                # Positif -> Lots A (plus jeunes d'abord : FIFO inverse sur date)
                temp_df = temp_df.sort_values(by='dt', ascending=False)
                # On ajoute l'écart sur le premier lot trouvé
                idx_to_adjust = temp_df.index[0]
                df_final.at[idx_to_adjust, col_qty] += ecart 
            
            else:
                # Négatif -> Lots AM (plus vieux d'abord : LIFO sur date)
                temp_df = temp_df.sort_values(by='dt', ascending=True)
                # Distribution dégressive du négatif
                rem_ecart = abs(ecart)
                for idx in temp_df.index:
                    current_val = df_final.at[idx, col_qty]
                    take = min(current_val, rem_ecart)
                    df_final.at[idx, col_qty] -= take
                    rem_ecart -= take
                    if rem_ecart <= 0: break
                
        # --- 3. FINAL OUTPUT FORMATTING (F vs G) ---
        # User Logic Update:
        # Col 5 (F): ALWAYS Original Theoretical Quantity (Restored)
        # Col 6 (G): ALWAYS Final Real Quantity (Calculated)
        
        # 1. Save Calculated Final Quantity to Col 6 (G)
        df_final[col_adj] = df_final[col_qty]
        
        # 2. Restore Original Quantity to Col 5 (F)
        # We use the preserved series.
        # Note: We must ensure alignment. df_final indicates 'S' lines might have moved? 
        # No, we only modified values in place or sorted temp_df but updated df_final using index.
        # So index alignment is preserved.
        df_final[col_qty] = original_qty_series
        
        # 2.5 INDICATOR LOGIC: Set to 2 for lots reduced to 0
        # After gap distribution, if a lot's final quantity (col_adj/6) is 0, set indicator to 2
        col_indicator = c(7)
        for idx in df_final.index:
            if df_final.at[idx, c(0)] == 'S':  # Only for stock lines
                final_qty = df_final.at[idx, col_adj]
                # Check if final quantity is 0 (or very close to 0)
                try:
                    if pd.notna(final_qty) and float(final_qty) == 0:
                        df_final.at[idx, col_indicator] = "2"
                except (ValueError, TypeError):
                    pass
        
        # --- 4. INTEGER CONVERSION ---
        # Helper to strict int conversion (empty string if NaN)
        def to_int_str(val):
            if pd.isna(val) or val == "":
                return ""
            try:
                # Handle cases like "12.0" or 12.0
                return str(int(round(float(val))))
            except (ValueError, TypeError):
                return ""

        df_final[col_qty] = df_final[col_qty].apply(to_int_str)
        df_final[col_adj] = df_final[col_adj].apply(to_int_str)

        return df_final