"""
Utilitaires pour les exports comptables (Excel et PDF).
"""
from io import BytesIO
from datetime import datetime
from decimal import Decimal

from django.http import HttpResponse
from django.utils import timezone

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def format_montant(value):
    """Formate un montant avec séparateur de milliers."""
    if value is None:
        return "0"
    try:
        value = int(value)
        return f"{value:,}".replace(',', ' ')
    except (ValueError, TypeError):
        return "0"


def export_rapport_gare_excel(donnees, filtres):
    """
    Exporte le rapport par gare en format Excel.

    Args:
        donnees: Liste des lignes de données du rapport
        filtres: Dictionnaire contenant les filtres appliqués
            - gare_nom: Nom de la gare (ou "Toutes les gares")
            - ligne_nom: Nom de la ligne (ou "Toutes les lignes")
            - date_debut: Date de début
            - date_fin: Date de fin
            - total_charge: Total des dépenses
            - total_versement: Total du bénéfice net
            - types_depenses: Liste des types de dépenses présents
            - colonnes: Liste des colonnes à afficher

    Returns:
        HttpResponse avec le fichier Excel
    """
    if not OPENPYXL_AVAILABLE:
        raise ImportError("openpyxl n'est pas installé. Installez-le avec: pip install openpyxl")

    # Créer le workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Rapport par gare"

    # Styles
    header_fill = PatternFill(start_color="1e3a5f", end_color="1e3a5f", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    total_fill = PatternFill(start_color="e2e8f0", end_color="e2e8f0", fill_type="solid")
    total_font = Font(bold=True, size=11)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # En-tête du rapport
    row = 1
    ws.merge_cells(f'A{row}:H{row}')
    cell = ws[f'A{row}']
    cell.value = "RAPPORT PAR GARE"
    cell.font = Font(bold=True, size=16)
    cell.alignment = Alignment(horizontal='center')

    row += 1
    ws.merge_cells(f'A{row}:H{row}')
    cell = ws[f'A{row}']
    if filtres['date_debut'] == filtres['date_fin']:
        cell.value = f"Gare: {filtres['gare_nom']} | Date: {filtres['date_debut'].strftime('%d/%m/%Y')} | Ligne: {filtres['ligne_nom']}"
    else:
        cell.value = f"Gare: {filtres['gare_nom']} | Du {filtres['date_debut'].strftime('%d/%m/%Y')} au {filtres['date_fin'].strftime('%d/%m/%Y')} | Ligne: {filtres['ligne_nom']}"
    cell.alignment = Alignment(horizontal='center')

    row += 1
    ws.merge_cells(f'A{row}:H{row}')
    cell = ws[f'A{row}']
    cell.value = f"Généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}"
    cell.font = Font(italic=True, size=9)
    cell.alignment = Alignment(horizontal='center')

    row += 2  # Ligne vide

    # En-têtes de colonnes
    col_index = 1
    for col_name in filtres['colonnes']:
        cell = ws.cell(row=row, column=col_index)
        cell.value = col_name
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = border
        col_index += 1

    # Ajuster la largeur des colonnes
    column_widths = {
        'Date': 12,
        'Gare': 15,
        'Ligne': 25,
        'Num Départ': 12,
        'Nb Pass.': 10,
        'Recette Billets': 15,
        'Recette Bagages': 15,
        'Total Dépenses': 15,
        'Bénéfice Net': 15,
    }

    for idx, col_name in enumerate(filtres['colonnes'], start=1):
        width = column_widths.get(col_name, 14)
        ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = width

    # Données
    row += 1
    for ligne_data in donnees:
        col_index = 1
        for col_name in filtres['colonnes']:
            cell = ws.cell(row=row, column=col_index)
            value = ligne_data.get(col_name, 0)

            # Formatage selon le type de colonne
            if col_name in ['Recette Billets', 'Recette Bagages', 'Total Dépenses', 'Bénéfice Net'] or 'Carburant' in col_name or 'Frais' in col_name or 'Ration' in col_name or 'Réparation' in col_name or 'Divers' in col_name:
                # Colonnes monétaires
                cell.value = int(value) if value else 0
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal='right')
            elif col_name == 'Nb Pass.':
                cell.value = int(value) if value else 0
                cell.alignment = Alignment(horizontal='center')
            else:
                cell.value = value
                cell.alignment = Alignment(horizontal='left')

            cell.border = border
            col_index += 1
        row += 1

    # Ligne de total
    if donnees:
        col_index = 1
        for col_name in filtres['colonnes']:
            cell = ws.cell(row=row, column=col_index)
            cell.fill = total_fill
            cell.font = total_font
            cell.border = border

            if col_name in ['Date', 'Gare', 'Ligne', 'Num Départ']:
                if col_index == 1:
                    cell.value = "TOTAL"
                    cell.alignment = Alignment(horizontal='center')
                else:
                    cell.value = ""
            elif col_name == 'Nb Pass.':
                cell.value = sum(int(d.get(col_name, 0)) for d in donnees)
                cell.alignment = Alignment(horizontal='center')
            elif col_name in ['Recette Billets', 'Recette Bagages', 'Total Dépenses', 'Bénéfice Net'] or any(x in col_name for x in ['Carburant', 'Frais', 'Ration', 'Réparation', 'Divers']):
                cell.value = sum(int(d.get(col_name, 0)) for d in donnees)
                cell.number_format = '#,##0'
                cell.alignment = Alignment(horizontal='right')
            else:
                cell.value = ""

            col_index += 1

        row += 2  # Lignes vides

        # Résumé final
        ws.merge_cells(f'A{row}:C{row}')
        cell = ws[f'A{row}']
        cell.value = "CHARGE GARE (Total Dépenses):"
        cell.font = Font(bold=True, size=12)
        cell.alignment = Alignment(horizontal='right')

        cell = ws[f'D{row}']
        cell.value = int(filtres['total_charge'])
        cell.font = Font(bold=True, size=12)
        cell.number_format = '#,##0" FCFA"'

        row += 1
        ws.merge_cells(f'A{row}:C{row}')
        cell = ws[f'A{row}']
        cell.value = "VERSEMENT (Bénéfice Net):"
        cell.font = Font(bold=True, size=12)
        cell.alignment = Alignment(horizontal='right')

        cell = ws[f'D{row}']
        cell.value = int(filtres['total_versement'])
        cell.font = Font(bold=True, size=12)
        cell.number_format = '#,##0" FCFA"'

    # Générer le fichier
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    # Nom du fichier
    gare_slug = filtres['gare_nom'].lower().replace(' ', '-').replace('è', 'e').replace('é', 'e')
    date_str = filtres['date_debut'].strftime('%Y%m%d')
    if filtres['date_debut'] != filtres['date_fin']:
        date_str += f"_{filtres['date_fin'].strftime('%Y%m%d')}"
    filename = f"rapport_gare_{gare_slug}_{date_str}.xlsx"

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


def export_rapport_gare_pdf(donnees, filtres):
    """
    Exporte le rapport par gare en format PDF.

    Args:
        donnees: Liste des lignes de données du rapport
        filtres: Dictionnaire contenant les filtres appliqués

    Returns:
        HttpResponse avec le fichier PDF
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab n'est pas installé. Installez-le avec: pip install reportlab")

    # Créer le document
    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # Conteneur pour les éléments
    elements = []
    styles = getSampleStyleSheet()

    # Style personnalisé pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e3a5f'),
        spaceAfter=12,
        alignment=1  # Centre
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=20,
        alignment=1
    )

    # Titre
    elements.append(Paragraph("RAPPORT PAR GARE", title_style))

    # Sous-titre avec filtres
    if filtres['date_debut'] == filtres['date_fin']:
        subtitle = f"Gare: {filtres['gare_nom']} | Date: {filtres['date_debut'].strftime('%d/%m/%Y')} | Ligne: {filtres['ligne_nom']}"
    else:
        subtitle = f"Gare: {filtres['gare_nom']} | Du {filtres['date_debut'].strftime('%d/%m/%Y')} au {filtres['date_fin'].strftime('%d/%m/%Y')} | Ligne: {filtres['ligne_nom']}"
    elements.append(Paragraph(subtitle, subtitle_style))

    # Préparer les données du tableau
    table_data = []

    # En-têtes
    headers = filtres['colonnes']
    table_data.append(headers)

    # Données
    for ligne_data in donnees:
        row = []
        for col_name in headers:
            value = ligne_data.get(col_name, 0)
            if col_name in ['Recette Billets', 'Recette Bagages', 'Total Dépenses', 'Bénéfice Net'] or any(x in col_name for x in ['Carburant', 'Frais', 'Ration', 'Réparation', 'Divers']):
                row.append(format_montant(value))
            else:
                row.append(str(value))
        table_data.append(row)

    # Ligne de total
    if donnees:
        total_row = []
        for col_name in headers:
            if col_name in ['Date', 'Gare', 'Ligne']:
                total_row.append("")
            elif col_name == 'Num Départ':
                total_row.append("TOTAL")
            elif col_name == 'Nb Pass.':
                total_row.append(str(sum(int(d.get(col_name, 0)) for d in donnees)))
            elif col_name in ['Recette Billets', 'Recette Bagages', 'Total Dépenses', 'Bénéfice Net'] or any(x in col_name for x in ['Carburant', 'Frais', 'Ration', 'Réparation', 'Divers']):
                total_row.append(format_montant(sum(int(d.get(col_name, 0)) for d in donnees)))
            else:
                total_row.append("")
        table_data.append(total_row)

    # Créer le tableau
    table = Table(table_data)

    # Style du tableau
    table_style = TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

        # Données
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 8),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),

        # Ligne de total
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 9),

        # Grille
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ])

    table.setStyle(table_style)
    elements.append(table)

    # Résumé final
    elements.append(Spacer(1, 0.5*cm))

    summary_data = [
        ['CHARGE GARE (Total Dépenses):', f"{format_montant(filtres['total_charge'])} FCFA"],
        ['VERSEMENT (Bénéfice Net):', f"{format_montant(filtres['total_versement'])} FCFA"]
    ]

    summary_table = Table(summary_data, colWidths=[8*cm, 5*cm])
    summary_style = TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ])
    summary_table.setStyle(summary_style)
    elements.append(summary_table)

    # Générer le PDF
    doc.build(elements)
    output.seek(0)

    # Nom du fichier
    gare_slug = filtres['gare_nom'].lower().replace(' ', '-').replace('è', 'e').replace('é', 'e')
    date_str = filtres['date_debut'].strftime('%Y%m%d')
    if filtres['date_debut'] != filtres['date_fin']:
        date_str += f"_{filtres['date_fin'].strftime('%Y%m%d')}"
    filename = f"rapport_gare_{gare_slug}_{date_str}.pdf"

    response = HttpResponse(output.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response
