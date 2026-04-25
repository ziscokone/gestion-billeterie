"""
Génération du contrat de maintenance professionnel — SGB
Usage : python3 generer_contrat_maintenance.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import date
import os

# ─── COULEURS ────────────────────────────────────────────────────────────────
BLEU_FONCE   = colors.HexColor("#0D2B55")
BLEU_MOYEN   = colors.HexColor("#1A4A8A")
BLEU_CLAIR   = colors.HexColor("#E8F0FB")
ORANGE       = colors.HexColor("#E07B00")
GRIS_TEXTE   = colors.HexColor("#2C2C2C")
GRIS_CLAIR   = colors.HexColor("#F4F6F9")
GRIS_BORDURE = colors.HexColor("#C8D0DC")
BLANC        = colors.white

# ─── INFORMATIONS À PERSONNALISER ────────────────────────────────────────────
PRESTATAIRE = {
    "nom":       "ZKONE TECH",                        # <-- Ton nom / société
    "adresse":   "Abidjan, Côte d'Ivoire",
    "tel":       "+225 07 XX XX XX XX",
    "email":     "contact@zkonetech.ci",
    "siret":     "RC/ABJ/XXXX/X/XXXXX",
}

# Ces champs seront remplis à la main sur le document imprimé
CLIENT = {
    "nom":          "________________________________",
    "raison":       "________________________________",
    "adresse":      "________________________________",
    "tel":          "________________________________",
    "email":        "________________________________",
    "representant": "________________________________",
    "fonction":     "________________________________",
}

DATE_CONTRAT  = date.today().strftime("%d/%m/%Y")
REF_CONTRAT   = "MAINT-2026-001"
DUREE_MOIS    = 12
DATE_DEBUT    = "___  /___  / 2026"
DATE_FIN      = "___  /___  / 2027"
OUTPUT_FILE   = "Contrat_Maintenance_SGB.pdf"

W, H = A4


# ─── CANVAS DE PAGE (en-tête + pied de page) ─────────────────────────────────
class PageCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page(num_pages)
            super().showPage()
        super().save()

    def _draw_page(self, total_pages):
        page_num = self._pageNumber

        # ── Bandeau en-tête ──
        self.setFillColor(BLEU_FONCE)
        self.rect(0, H - 22*mm, W, 22*mm, fill=True, stroke=False)

        # Titre dans le bandeau
        self.setFillColor(BLANC)
        self.setFont("Helvetica-Bold", 11)
        self.drawString(15*mm, H - 13*mm, "CONTRAT DE MAINTENANCE & SUPPORT — SYSTÈME DE GESTION DE BILLETTERIE")

        # Ref à droite
        self.setFont("Helvetica", 8)
        self.drawRightString(W - 15*mm, H - 13*mm, f"Réf. : {REF_CONTRAT}")

        # Trait orange sous le bandeau
        self.setStrokeColor(ORANGE)
        self.setLineWidth(2)
        self.line(0, H - 23*mm, W, H - 23*mm)

        # ── Pied de page ──
        self.setStrokeColor(GRIS_BORDURE)
        self.setLineWidth(0.5)
        self.line(15*mm, 14*mm, W - 15*mm, 14*mm)

        self.setFillColor(GRIS_TEXTE)
        self.setFont("Helvetica", 7.5)
        self.drawString(15*mm, 9*mm, f"{PRESTATAIRE['nom']}  |  {PRESTATAIRE['adresse']}  |  {PRESTATAIRE['tel']}")
        self.drawRightString(W - 15*mm, 9*mm, f"Page {page_num} / {total_pages}")

        # Filigrane sur page de couverture
        if page_num == 1:
            self.saveState()
            self.setFillColor(colors.HexColor("#0D2B55"))
            self.setFillAlpha(0.04)
            self.setFont("Helvetica-Bold", 80)
            self.translate(W/2, H/2)
            self.rotate(40)
            self.drawCentredString(0, 0, "CONFIDENTIEL")
            self.restoreState()


# ─── STYLES ──────────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    styles = {}

    styles["titre_contrat"] = ParagraphStyle(
        "titre_contrat",
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=BLEU_FONCE,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    styles["sous_titre"] = ParagraphStyle(
        "sous_titre",
        fontName="Helvetica",
        fontSize=12,
        textColor=BLEU_MOYEN,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    styles["ref_date"] = ParagraphStyle(
        "ref_date",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#666666"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    styles["section_titre"] = ParagraphStyle(
        "section_titre",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=BLANC,
        alignment=TA_LEFT,
        leftIndent=6,
        leading=14,
    )
    styles["article_titre"] = ParagraphStyle(
        "article_titre",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=BLEU_FONCE,
        spaceBefore=8,
        spaceAfter=4,
    )
    styles["corps"] = ParagraphStyle(
        "corps",
        fontName="Helvetica",
        fontSize=9.5,
        textColor=GRIS_TEXTE,
        alignment=TA_JUSTIFY,
        leading=15,
        spaceAfter=4,
    )
    styles["corps_bold"] = ParagraphStyle(
        "corps_bold",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        textColor=GRIS_TEXTE,
        leading=15,
    )
    styles["puce"] = ParagraphStyle(
        "puce",
        fontName="Helvetica",
        fontSize=9.5,
        textColor=GRIS_TEXTE,
        leftIndent=14,
        leading=15,
        spaceAfter=2,
    )
    styles["note"] = ParagraphStyle(
        "note",
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        textColor=colors.HexColor("#666666"),
        alignment=TA_JUSTIFY,
        leading=13,
    )
    styles["signature_label"] = ParagraphStyle(
        "signature_label",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=BLEU_FONCE,
        alignment=TA_CENTER,
    )
    styles["signature_champ"] = ParagraphStyle(
        "signature_champ",
        fontName="Helvetica",
        fontSize=9,
        textColor=GRIS_TEXTE,
        alignment=TA_LEFT,
        leading=16,
    )
    return styles


# ─── COMPOSANTS RÉUTILISABLES ─────────────────────────────────────────────────
def bandeau_section(texte, styles):
    """Bandeau de titre de section (fond bleu foncé)."""
    data = [[Paragraph(texte, styles["section_titre"])]]
    t = Table(data, colWidths=[W - 30*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), BLEU_FONCE),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW",   (0, 0), (-1, -1), 2, ORANGE),
    ]))
    return t


def ligne_info(label, valeur, styles):
    """Ligne label : valeur."""
    data = [[
        Paragraph(f"<b>{label}</b>", styles["corps"]),
        Paragraph(valeur, styles["corps"]),
    ]]
    t = Table(data, colWidths=[50*mm, W - 30*mm - 55*mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def puce(texte, styles):
    return Paragraph(f"<font color='#E07B00'>&#9654;</font>  {texte}", styles["puce"])


def sp(n=1):
    return Spacer(1, n * 4*mm)


# ─── CONSTRUCTION DU DOCUMENT ─────────────────────────────────────────────────
def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=27*mm,
        bottomMargin=20*mm,
        title="Contrat de Maintenance - SGB",
        author=PRESTATAIRE["nom"],
    )

    S = build_styles()
    story = []

    # ══════════════════════════════════════════════════════════════
    # PAGE DE COUVERTURE
    # ══════════════════════════════════════════════════════════════
    story.append(sp(6))

    # Bloc logo / identité prestataire
    logo_bloc = Table([[
        Paragraph(
            f"<font size=18><b>{PRESTATAIRE['nom']}</b></font><br/>"
            f"<font size=9 color='#666666'>{PRESTATAIRE['adresse']}</font>",
            ParagraphStyle("lp", fontName="Helvetica-Bold", fontSize=18, textColor=BLEU_FONCE, leading=20)
        ),
        Paragraph(
            f"<font size=8 color='#666666'>"
            f"Tél : {PRESTATAIRE['tel']}<br/>"
            f"Email : {PRESTATAIRE['email']}<br/>"
            f"RC : {PRESTATAIRE['siret']}"
            f"</font>",
            ParagraphStyle("rp", fontName="Helvetica", fontSize=8, textColor=GRIS_TEXTE, alignment=TA_RIGHT, leading=13)
        ),
    ]], colWidths=[(W - 30*mm) * 0.55, (W - 30*mm) * 0.45])
    logo_bloc.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, GRIS_BORDURE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(logo_bloc)
    story.append(sp(5))

    # Titre principal
    story.append(Paragraph("CONTRAT DE MAINTENANCE", S["titre_contrat"]))
    story.append(Paragraph("ET DE SUPPORT TECHNIQUE", S["titre_contrat"]))
    story.append(sp(1))
    story.append(Paragraph("Système de Gestion de Billetterie (SGB)", S["sous_titre"]))
    story.append(sp(1))

    # Trait décoratif
    story.append(HRFlowable(width="100%", thickness=2, color=ORANGE, spaceAfter=6))

    story.append(Paragraph(f"Référence : <b>{REF_CONTRAT}</b>  |  Date : <b>{DATE_CONTRAT}</b>", S["ref_date"]))
    story.append(sp(4))

    # Encadré parties
    parties_data = [
        [
            Paragraph("<b>LE PRESTATAIRE</b>", ParagraphStyle("ph", fontName="Helvetica-Bold", fontSize=10, textColor=BLANC, alignment=TA_CENTER)),
            Paragraph("<b>LE CLIENT</b>", ParagraphStyle("ph", fontName="Helvetica-Bold", fontSize=10, textColor=BLANC, alignment=TA_CENTER)),
        ],
        [
            Paragraph(
                f"<b>{PRESTATAIRE['nom']}</b><br/>"
                f"{PRESTATAIRE['adresse']}<br/>"
                f"Tél : {PRESTATAIRE['tel']}<br/>"
                f"Email : {PRESTATAIRE['email']}",
                ParagraphStyle("pc", fontName="Helvetica", fontSize=9, textColor=GRIS_TEXTE, leading=14, alignment=TA_LEFT)
            ),
            Paragraph(
                f"<b>Raison sociale :</b> {CLIENT['raison']}<br/>"
                f"<b>Représentant :</b> {CLIENT['representant']}<br/>"
                f"<b>Fonction :</b> {CLIENT['fonction']}<br/>"
                f"<b>Adresse :</b> {CLIENT['adresse']}<br/>"
                f"<b>Tél :</b> {CLIENT['tel']}",
                ParagraphStyle("cc", fontName="Helvetica", fontSize=9, textColor=GRIS_TEXTE, leading=14, alignment=TA_LEFT)
            ),
        ]
    ]
    col = (W - 30*mm) / 2
    parties_t = Table(parties_data, colWidths=[col, col])
    parties_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BLEU_FONCE),
        ("BACKGROUND",    (0, 1), (0, 1), BLEU_CLAIR),
        ("BACKGROUND",    (1, 1), (1, 1), GRIS_CLAIR),
        ("GRID",          (0, 0), (-1, -1), 0.5, GRIS_BORDURE),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW",     (0, 0), (-1, -1), 2, ORANGE),
    ]))
    story.append(parties_t)
    story.append(sp(4))

    # Résumé financier couverture
    resume_data = [
        [Paragraph("<b>SYNTHÈSE CONTRACTUELLE</b>", ParagraphStyle("sh", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_CENTER)), "", ""],
        [
            Paragraph("<b>Durée</b>", ParagraphStyle("sl", fontName="Helvetica-Bold", fontSize=9, textColor=BLEU_FONCE, alignment=TA_CENTER)),
            Paragraph("<b>Date de début</b>", ParagraphStyle("sl", fontName="Helvetica-Bold", fontSize=9, textColor=BLEU_FONCE, alignment=TA_CENTER)),
            Paragraph("<b>Date de fin</b>", ParagraphStyle("sl", fontName="Helvetica-Bold", fontSize=9, textColor=BLEU_FONCE, alignment=TA_CENTER)),
        ],
        [
            Paragraph(f"{DUREE_MOIS} mois", ParagraphStyle("sv", fontName="Helvetica-Bold", fontSize=11, textColor=ORANGE, alignment=TA_CENTER)),
            Paragraph(DATE_DEBUT, ParagraphStyle("sv", fontName="Helvetica", fontSize=10, textColor=GRIS_TEXTE, alignment=TA_CENTER)),
            Paragraph(DATE_FIN, ParagraphStyle("sv", fontName="Helvetica", fontSize=10, textColor=GRIS_TEXTE, alignment=TA_CENTER)),
        ],
    ]
    col3 = (W - 30*mm) / 3
    resume_t = Table(resume_data, colWidths=[col3, col3, col3])
    resume_t.setStyle(TableStyle([
        ("SPAN",          (0, 0), (2, 0)),
        ("BACKGROUND",    (0, 0), (-1, 0), BLEU_FONCE),
        ("BACKGROUND",    (0, 1), (-1, 1), BLEU_CLAIR),
        ("GRID",          (0, 0), (-1, -1), 0.5, GRIS_BORDURE),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(resume_t)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # PRÉAMBULE
    # ══════════════════════════════════════════════════════════════
    story.append(bandeau_section("PRÉAMBULE", S))
    story.append(sp(1))
    story.append(Paragraph(
        "Le présent contrat est conclu entre les parties désignées ci-dessus en vue de définir les conditions "
        "et modalités selon lesquelles le Prestataire assure la maintenance, le support technique et l'hébergement "
        "du Système de Gestion de Billetterie (SGB) déployé au profit du Client.",
        S["corps"]
    ))
    story.append(Paragraph(
        "Le SGB est une application web de gestion complète des opérations de transport : vente et réservation de billets, "
        "gestion des voyages et des lignes, rapports financiers, gestion du personnel et de la flotte. "
        "Le Client reconnaît avoir pris connaissance des fonctionnalités de la solution avant la signature du présent contrat.",
        S["corps"]
    ))
    story.append(sp(2))

    # ══════════════════════════════════════════════════════════════
    # ARTICLE 1 — OBJET DU CONTRAT
    # ══════════════════════════════════════════════════════════════
    story.append(bandeau_section("ARTICLE 1 — OBJET DU CONTRAT", S))
    story.append(sp(1))
    story.append(Paragraph(
        "Le présent contrat a pour objet de définir les prestations de maintenance corrective, évolutive et de support "
        "technique assurées par le Prestataire sur le Système de Gestion de Billetterie (SGB) du Client, "
        "ainsi que les conditions d'hébergement de ladite application.",
        S["corps"]
    ))
    story.append(sp(2))

    # ══════════════════════════════════════════════════════════════
    # ARTICLE 2 — PÉRIMÈTRE DES PRESTATIONS
    # ══════════════════════════════════════════════════════════════
    story.append(bandeau_section("ARTICLE 2 — PÉRIMÈTRE DES PRESTATIONS", S))
    story.append(sp(1))

    prestations = [
        ("2.1  Maintenance corrective",
         "Correction de tout dysfonctionnement avéré de l'application dans les délais contractuels définis à "
         "l'article 4. Sont concernés : les bugs bloquants, les erreurs d'affichage, les incohérences de données "
         "et tout comportement anormal du système."),
        ("2.2  Maintenance évolutive (mises à jour)",
         "Déploiement des mises à jour de sécurité et des corrections mineures d'amélioration de l'interface. "
         "Les évolutions fonctionnelles majeures (nouveaux modules) font l'objet d'un devis séparé."),
        ("2.3  Hébergement et disponibilité",
         "Hébergement de l'application sur serveur sécurisé avec un engagement de disponibilité de 99 % "
         "hors maintenances planifiées notifiées au préalable."),
        ("2.4  Sauvegardes automatiques",
         "Sauvegarde complète de la base de données du Client réalisée quotidiennement. "
         "Conservation des sauvegardes sur une période de 30 jours glissants."),
        ("2.5  Support technique",
         "Assistance technique aux utilisateurs du Client par WhatsApp, e-mail ou téléphone, "
         "selon les plages horaires et délais de réponse définis à l'article 4."),
        ("2.6  Administration des gares",
         "Ajout ou modification de paramètres mineurs (tarifs, horaires, comptes utilisateurs) "
         "dans la limite de 5 opérations simples par mois. Au-delà, une facturation complémentaire s'applique."),
    ]

    for titre_art, texte_art in prestations:
        story.append(Paragraph(f"<b>{titre_art}</b>", S["article_titre"]))
        story.append(Paragraph(texte_art, S["corps"]))

    story.append(sp(1))
    story.append(Paragraph(
        "<b>Sont exclus du périmètre de ce contrat :</b> les développements de nouvelles fonctionnalités, "
        "la formation de nouveaux utilisateurs, le matériel informatique du Client, les pannes de connexion internet "
        "imputables au fournisseur d'accès du Client.",
        S["note"]
    ))
    story.append(sp(2))

    # ══════════════════════════════════════════════════════════════
    # ARTICLE 3 — CONDITIONS FINANCIÈRES
    # ══════════════════════════════════════════════════════════════
    story.append(bandeau_section("ARTICLE 3 — CONDITIONS FINANCIÈRES", S))
    story.append(sp(1))

    # ── 3.1 FRAIS DE CONFIGURATION PAR GARE ──────────────────────
    story.append(Paragraph("<b>3.1  Frais de configuration et de mise en service par gare</b>", S["article_titre"]))
    story.append(Paragraph(
        "Préalablement à toute mise en service, chaque gare exploitée sur le SGB fait l'objet d'une "
        "prestation de configuration facturée séparément et une seule fois. Cette prestation couvre :",
        S["corps"]
    ))
    for item in [
        "Création et paramétrage de la gare dans le système (nom, code, souche de tickets)",
        "Configuration de toutes les lignes au départ de cette gare",
        "Saisie des destinations desservies et des tarifs correspondants",
        "Création des comptes utilisateurs (guichetiers, chef de gare)",
        "Formation du personnel de la gare (1 journée sur site ou à distance)",
        "Tests de validation et mise en production de la gare",
    ]:
        story.append(puce(item, S))
    story.append(sp(1))

    # Encadré tarifaire 500 000 FCFA — bien visible
    tarif_config_data = [
        [
            Paragraph(
                "FRAIS DE CONFIGURATION",
                ParagraphStyle("fct", fontName="Helvetica-Bold", fontSize=10, textColor=BLANC, alignment=TA_CENTER)
            ),
            Paragraph(
                "500 000 FCFA",
                ParagraphStyle("fcp", fontName="Helvetica-Bold", fontSize=22, textColor=ORANGE, alignment=TA_CENTER)
            ),
            Paragraph(
                "PAR GARE\n(paiement unique à la commande)",
                ParagraphStyle("fcu", fontName="Helvetica", fontSize=9, textColor=BLANC, alignment=TA_CENTER, leading=14)
            ),
        ],
    ]
    config_t = Table(
        tarif_config_data,
        colWidths=[(W - 30*mm) * f for f in [0.42, 0.30, 0.28]]
    )
    config_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), BLEU_FONCE),
        ("BACKGROUND",    (1, 0), (1, 0), colors.HexColor("#0D2B55")),
        ("BACKGROUND",    (2, 0), (2, 0), BLEU_MOYEN),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW",     (0, 0), (-1, -1), 3, ORANGE),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#ffffff")),
    ]))
    story.append(config_t)
    story.append(sp(1))

    # Tableau récapitulatif des gares du contrat
    story.append(Paragraph(
        "<b>Gares couvertes par le présent contrat :</b>",
        S["corps_bold"]
    ))
    story.append(sp(1))

    gares_config_data = [
        [
            Paragraph("<b>N°</b>", ParagraphStyle("gh", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_CENTER)),
            Paragraph("<b>Nom de la gare</b>", ParagraphStyle("gh", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_CENTER)),
            Paragraph("<b>Ville / Localité</b>", ParagraphStyle("gh", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_CENTER)),
            Paragraph("<b>Frais de configuration</b>", ParagraphStyle("gh", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_CENTER)),
        ],
    ]
    for i in range(1, 5):
        bg = BLEU_CLAIR if i % 2 == 0 else BLANC
        gares_config_data.append([
            Paragraph(str(i), ParagraphStyle(f"gn{i}", fontName="Helvetica-Bold", fontSize=9, textColor=BLEU_FONCE, alignment=TA_CENTER)),
            Paragraph("________________________________", ParagraphStyle(f"gv{i}", fontName="Helvetica", fontSize=9, textColor=GRIS_TEXTE)),
            Paragraph("________________________________", ParagraphStyle(f"gl{i}", fontName="Helvetica", fontSize=9, textColor=GRIS_TEXTE)),
            Paragraph("500 000 FCFA", ParagraphStyle(f"gp{i}", fontName="Helvetica-Bold", fontSize=9, textColor=ORANGE, alignment=TA_CENTER)),
        ])

    # Ligne total
    gares_config_data.append([
        Paragraph("", ParagraphStyle("gt0", fontName="Helvetica", fontSize=9)),
        Paragraph("", ParagraphStyle("gt1", fontName="Helvetica", fontSize=9)),
        Paragraph("<b>TOTAL CONFIGURATION</b>", ParagraphStyle("gtt", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_RIGHT)),
        Paragraph("_______ × 500 000 FCFA\n= _____________ FCFA", ParagraphStyle("gtp", fontName="Helvetica-Bold", fontSize=9, textColor=ORANGE, alignment=TA_CENTER, leading=13)),
    ])

    cw_g = [(W - 30*mm) * f for f in [0.07, 0.37, 0.30, 0.26]]
    gares_t = Table(gares_config_data, colWidths=cw_g)
    gares_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BLEU_FONCE),
        ("ROWBACKGROUNDS",(0, 1), (-1, -2), [BLANC, BLEU_CLAIR]),
        ("BACKGROUND",    (0, -1), (-1, -1), BLEU_MOYEN),
        ("GRID",          (0, 0), (-1, -1), 0.5, GRIS_BORDURE),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW",     (0, 0), (-1, 0), 2, ORANGE),
        ("LINEABOVE",     (0, -1), (-1, -1), 1.5, ORANGE),
    ]))
    story.append(gares_t)
    story.append(sp(1))
    story.append(Paragraph(
        "Les frais de configuration sont dus à la signature du bon de commande et ne sont pas remboursables. "
        "Toute gare supplémentaire ouverte après la signature du présent contrat fera l'objet d'une nouvelle "
        "facturation de <b>500 000 FCFA</b> par gare, indépendamment du contrat de maintenance.",
        S["note"]
    ))
    story.append(sp(2))

    # ── 3.2 REDEVANCE MENSUELLE DE MAINTENANCE ────────────────────
    story.append(Paragraph("<b>3.2  Redevance mensuelle de maintenance</b>", S["article_titre"]))
    story.append(Paragraph(
        "La redevance de maintenance est établie en fonction du nombre de gares actives couvertes par le présent contrat. "
        "Une dégressivité est appliquée pour encourager les compagnies multi-gares.",
        S["corps"]
    ))
    story.append(sp(1))

    # Tableau tarifs maintenance
    tarifs_header = [
        Paragraph("<b>Nombre de gares</b>", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_CENTER)),
        Paragraph("<b>Tarif mensuel / gare</b>", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_CENTER)),
        Paragraph("<b>Tarif mensuel total</b>", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_CENTER)),
        Paragraph("<b>Tarif annuel (–10 %)</b>", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_CENTER)),
    ]
    tarifs_rows = [
        ["1 gare", "40 000 FCFA", "40 000 FCFA", "432 000 FCFA"],
        ["2 – 3 gares", "35 000 FCFA", "70 000 – 105 000 FCFA", "756 000 – 1 134 000 FCFA"],
        ["4 – 6 gares", "30 000 FCFA", "120 000 – 180 000 FCFA", "1 296 000 – 1 944 000 FCFA"],
        ["7 gares et plus", "Sur devis", "Sur devis", "Sur devis"],
    ]

    def fmt_tarif_row(row, idx):
        bg = BLEU_CLAIR if idx % 2 == 0 else BLANC
        return [
            Paragraph(row[0], ParagraphStyle("tr", fontName="Helvetica-Bold", fontSize=9, textColor=BLEU_FONCE, alignment=TA_CENTER)),
            Paragraph(row[1], ParagraphStyle("tr", fontName="Helvetica", fontSize=9, textColor=GRIS_TEXTE, alignment=TA_CENTER)),
            Paragraph(row[2], ParagraphStyle("tr", fontName="Helvetica-Bold", fontSize=9, textColor=ORANGE, alignment=TA_CENTER)),
            Paragraph(row[3], ParagraphStyle("tr", fontName="Helvetica", fontSize=9, textColor=GRIS_TEXTE, alignment=TA_CENTER)),
        ]

    tarif_data = [tarifs_header] + [fmt_tarif_row(r, i) for i, r in enumerate(tarifs_rows)]
    cw = (W - 30*mm) / 4
    tarif_t = Table(tarif_data, colWidths=[cw, cw, cw, cw])
    tarif_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BLEU_FONCE),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [BLEU_CLAIR, BLANC]),
        ("GRID",          (0, 0), (-1, -1), 0.5, GRIS_BORDURE),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW",     (0, 0), (-1, 0), 2, ORANGE),
    ]))
    story.append(tarif_t)
    story.append(sp(1))

    # Récap financier du présent contrat
    story.append(Paragraph("<b>Récapitulatif financier du présent contrat :</b>", S["corps_bold"]))
    story.append(sp(1))

    contrat_data = [
        [
            Paragraph("<b>Poste</b>", ParagraphStyle("ch", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_LEFT)),
            Paragraph("<b>Détail</b>", ParagraphStyle("ch", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_CENTER)),
            Paragraph("<b>Montant</b>", ParagraphStyle("ch", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_CENTER)),
        ],
        [
            Paragraph("Frais de configuration (une seule fois)", ParagraphStyle("cv1", fontName="Helvetica", fontSize=9, textColor=GRIS_TEXTE)),
            Paragraph("_______ gare(s) × 500 000 FCFA", ParagraphStyle("cv2", fontName="Helvetica", fontSize=9, textColor=GRIS_TEXTE, alignment=TA_CENTER)),
            Paragraph("_____________ FCFA", ParagraphStyle("cv3", fontName="Helvetica-Bold", fontSize=9, textColor=ORANGE, alignment=TA_CENTER)),
        ],
        [
            Paragraph("Redevance de maintenance mensuelle", ParagraphStyle("cv1b", fontName="Helvetica", fontSize=9, textColor=GRIS_TEXTE)),
            Paragraph("_______ gare(s) × _______ FCFA", ParagraphStyle("cv2b", fontName="Helvetica", fontSize=9, textColor=GRIS_TEXTE, alignment=TA_CENTER)),
            Paragraph("_____________ FCFA / mois", ParagraphStyle("cv3b", fontName="Helvetica-Bold", fontSize=9, textColor=ORANGE, alignment=TA_CENTER)),
        ],
        [
            Paragraph("<b>Modalité de paiement de la maintenance</b>", ParagraphStyle("cv1c", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC)),
            Paragraph("Mensuel  ☐          Annuel (–10 %)  ☐", ParagraphStyle("cv2c", fontName="Helvetica", fontSize=9, textColor=BLANC, alignment=TA_CENTER)),
            Paragraph("", ParagraphStyle("cv3c", fontName="Helvetica", fontSize=9)),
        ],
    ]
    cw2a = [(W - 30*mm) * f for f in [0.45, 0.32, 0.23]]
    contrat_t = Table(contrat_data, colWidths=cw2a)
    contrat_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BLEU_FONCE),
        ("BACKGROUND",    (0, -1), (-1, -1), BLEU_MOYEN),
        ("ROWBACKGROUNDS",(0, 1), (-1, -2), [BLANC, BLEU_CLAIR]),
        ("GRID",          (0, 0), (-1, -1), 0.5, GRIS_BORDURE),
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEABOVE",     (0, 0), (-1, 0), 2, BLEU_FONCE),
        ("LINEBELOW",     (0, -1), (-1, -1), 2, ORANGE),
    ]))
    story.append(contrat_t)
    story.append(sp(2))

    # ══════════════════════════════════════════════════════════════
    # ARTICLE 4 — NIVEAUX DE SERVICE (SLA)
    # ══════════════════════════════════════════════════════════════
    story.append(bandeau_section("ARTICLE 4 — NIVEAUX DE SERVICE (SLA)", S))
    story.append(sp(1))

    sla_data = [
        [
            Paragraph("<b>Priorité</b>", ParagraphStyle("sh", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_CENTER)),
            Paragraph("<b>Définition</b>", ParagraphStyle("sh", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_CENTER)),
            Paragraph("<b>Délai de prise en charge</b>", ParagraphStyle("sh", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_CENTER)),
            Paragraph("<b>Délai de résolution cible</b>", ParagraphStyle("sh", fontName="Helvetica-Bold", fontSize=9, textColor=BLANC, alignment=TA_CENTER)),
        ],
        [
            Paragraph("P1 — CRITIQUE", ParagraphStyle("p1", fontName="Helvetica-Bold", fontSize=9, textColor=colors.red, alignment=TA_CENTER)),
            Paragraph("Application inaccessible, perte de données, blocage total des ventes", ParagraphStyle("pd", fontName="Helvetica", fontSize=8.5, textColor=GRIS_TEXTE)),
            Paragraph("2 heures", ParagraphStyle("pt", fontName="Helvetica-Bold", fontSize=9, textColor=GRIS_TEXTE, alignment=TA_CENTER)),
            Paragraph("4 heures ouvrées", ParagraphStyle("pt", fontName="Helvetica", fontSize=9, textColor=GRIS_TEXTE, alignment=TA_CENTER)),
        ],
        [
            Paragraph("P2 — MAJEUR", ParagraphStyle("p2", fontName="Helvetica-Bold", fontSize=9, textColor=ORANGE, alignment=TA_CENTER)),
            Paragraph("Fonctionnalité importante indisponible, dégradation significative", ParagraphStyle("pd", fontName="Helvetica", fontSize=8.5, textColor=GRIS_TEXTE)),
            Paragraph("4 heures ouvrées", ParagraphStyle("pt", fontName="Helvetica-Bold", fontSize=9, textColor=GRIS_TEXTE, alignment=TA_CENTER)),
            Paragraph("24 heures ouvrées", ParagraphStyle("pt", fontName="Helvetica", fontSize=9, textColor=GRIS_TEXTE, alignment=TA_CENTER)),
        ],
        [
            Paragraph("P3 — MINEUR", ParagraphStyle("p3", fontName="Helvetica-Bold", fontSize=9, textColor=BLEU_MOYEN, alignment=TA_CENTER)),
            Paragraph("Anomalie mineure sans impact sur l'exploitation quotidienne", ParagraphStyle("pd", fontName="Helvetica", fontSize=8.5, textColor=GRIS_TEXTE)),
            Paragraph("Jour ouvré suivant", ParagraphStyle("pt", fontName="Helvetica-Bold", fontSize=9, textColor=GRIS_TEXTE, alignment=TA_CENTER)),
            Paragraph("5 jours ouvrés", ParagraphStyle("pt", fontName="Helvetica", fontSize=9, textColor=GRIS_TEXTE, alignment=TA_CENTER)),
        ],
    ]
    cols_sla = [(W - 30*mm) * f for f in [0.15, 0.40, 0.22, 0.23]]
    sla_t = Table(sla_data, colWidths=cols_sla)
    sla_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BLEU_FONCE),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [BLEU_CLAIR, BLANC, GRIS_CLAIR]),
        ("GRID",          (0, 0), (-1, -1), 0.5, GRIS_BORDURE),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW",     (0, 0), (-1, 0), 2, ORANGE),
    ]))
    story.append(sla_t)
    story.append(sp(1))
    story.append(Paragraph(
        "Les délais courent du lundi au vendredi, de 08h00 à 18h00 (heure d'Abidjan), hors jours fériés. "
        "Les incidents critiques (P1) sont traités en dehors de ces plages horaires dans la mesure du possible.",
        S["note"]
    ))
    story.append(sp(2))

    # ══════════════════════════════════════════════════════════════
    # ARTICLE 5 — MODALITÉS DE PAIEMENT
    # ══════════════════════════════════════════════════════════════
    story.append(bandeau_section("ARTICLE 5 — MODALITÉS DE PAIEMENT", S))
    story.append(sp(1))

    for pt_texte in [
        "Le paiement est dû en début de période (mensuelle ou annuelle) selon la modalité choisie.",
        "En cas de paiement annuel, une réduction de <b>10 %</b> est appliquée sur le montant total.",
        "Modes de paiement acceptés : virement bancaire, Orange Money Business, MTN Mobile Money Business, chèque certifié.",
        "Tout retard de paiement supérieur à <b>15 jours calendaires</b> autorise le Prestataire à suspendre les services "
        "après notification écrite au Client (WhatsApp ou e-mail). Les services sont rétablis dans les <b>24 heures</b> "
        "suivant la régularisation.",
        "Tout mois commencé est dû en intégralité.",
    ]:
        story.append(puce(pt_texte, S))
    story.append(sp(2))

    # ══════════════════════════════════════════════════════════════
    # ARTICLE 6 — DURÉE ET RENOUVELLEMENT
    # ══════════════════════════════════════════════════════════════
    story.append(bandeau_section("ARTICLE 6 — DURÉE ET RENOUVELLEMENT", S))
    story.append(sp(1))
    story.append(Paragraph(
        f"Le présent contrat est conclu pour une durée initiale de <b>{DUREE_MOIS} mois</b>, "
        f"à compter de la date de signature. À l'issue de cette période, il se renouvelle "
        "automatiquement par tacite reconduction pour des périodes successives d'un (1) an, "
        "sauf dénonciation par l'une des parties dans les conditions de l'article 8.",
        S["corps"]
    ))
    story.append(sp(2))

    # ══════════════════════════════════════════════════════════════
    # ARTICLE 7 — OBLIGATIONS DES PARTIES
    # ══════════════════════════════════════════════════════════════
    story.append(bandeau_section("ARTICLE 7 — OBLIGATIONS DES PARTIES", S))
    story.append(sp(1))

    story.append(Paragraph("<b>7.1  Obligations du Prestataire</b>", S["article_titre"]))
    for pt_texte in [
        "Assurer la disponibilité et la sécurité de l'application conformément aux engagements de niveau de service.",
        "Informer le Client de toute maintenance planifiée au moins <b>48 heures</b> à l'avance.",
        "Garantir la confidentialité des données du Client.",
        "Fournir un rapport mensuel d'incidents et d'interventions sur demande.",
        "Ne pas divulguer à des tiers les informations commerciales et opérationnelles du Client.",
    ]:
        story.append(puce(pt_texte, S))

    story.append(sp(1))
    story.append(Paragraph("<b>7.2  Obligations du Client</b>", S["article_titre"]))
    for pt_texte in [
        "Régler les redevances dans les délais convenus.",
        "Désigner un interlocuteur technique référent pour la remontée des incidents.",
        "Ne pas modifier, copier ou tenter de décompiler l'application sans accord écrit du Prestataire.",
        "Informer le Prestataire de tout changement d'organisation susceptible d'impacter l'utilisation du SGB.",
        "S'assurer que les postes de travail disposent d'une connexion internet stable et d'un navigateur à jour.",
    ]:
        story.append(puce(pt_texte, S))
    story.append(sp(2))

    # ══════════════════════════════════════════════════════════════
    # ARTICLE 8 — RÉSILIATION
    # ══════════════════════════════════════════════════════════════
    story.append(bandeau_section("ARTICLE 8 — RÉSILIATION", S))
    story.append(sp(1))

    story.append(Paragraph("<b>8.1  Résiliation à l'initiative du Client</b>", S["article_titre"]))
    story.append(Paragraph(
        "Le Client peut résilier le présent contrat par notification écrite adressée au Prestataire "
        "avec un préavis de <b>deux (2) mois</b>. En cas de résiliation anticipée durant la période initiale, "
        "les mensualités restantes jusqu'au terme de la période initiale sont dues.",
        S["corps"]
    ))

    story.append(Paragraph("<b>8.2  Résiliation à l'initiative du Prestataire</b>", S["article_titre"]))
    story.append(Paragraph(
        "Le Prestataire peut résilier le contrat en cas de manquement grave du Client à ses obligations "
        "(notamment non-paiement), après mise en demeure restée sans effet pendant <b>15 jours</b>.",
        S["corps"]
    ))

    story.append(Paragraph("<b>8.3  Effets de la résiliation</b>", S["article_titre"]))
    story.append(Paragraph(
        "À la date d'effet de la résiliation, le Prestataire procède à la remise au Client d'une "
        "sauvegarde complète de ses données dans un format standard (CSV / JSON) dans un délai de "
        "<b>15 jours ouvrés</b>. L'accès à l'application est maintenu jusqu'à la date d'effet.",
        S["corps"]
    ))
    story.append(sp(2))

    # ══════════════════════════════════════════════════════════════
    # ARTICLE 9 — CONFIDENTIALITÉ ET PROPRIÉTÉ DES DONNÉES
    # ══════════════════════════════════════════════════════════════
    story.append(bandeau_section("ARTICLE 9 — CONFIDENTIALITÉ ET PROPRIÉTÉ DES DONNÉES", S))
    story.append(sp(1))
    story.append(Paragraph(
        "Les données saisies dans le SGB (billets, voyages, clients, finances) demeurent la propriété exclusive "
        "du Client. Le Prestataire s'interdit toute exploitation commerciale ou communication de ces données à des tiers.",
        S["corps"]
    ))
    story.append(Paragraph(
        "Le logiciel SGB (code source, algorithmes, interfaces) reste la propriété intellectuelle exclusive du Prestataire. "
        "Le présent contrat confère au Client un droit d'usage de l'application, non exclusif et non transférable.",
        S["corps"]
    ))
    story.append(sp(2))

    # ══════════════════════════════════════════════════════════════
    # ARTICLE 10 — RESPONSABILITÉ ET FORCE MAJEURE
    # ══════════════════════════════════════════════════════════════
    story.append(bandeau_section("ARTICLE 10 — RESPONSABILITÉ ET FORCE MAJEURE", S))
    story.append(sp(1))
    story.append(Paragraph(
        "La responsabilité du Prestataire est limitée aux montants perçus au titre du présent contrat sur "
        "les trois (3) derniers mois. Le Prestataire ne saurait être tenu responsable des pertes d'exploitation "
        "indirectes du Client.",
        S["corps"]
    ))
    story.append(Paragraph(
        "Aucune des parties ne sera tenue responsable des manquements résultant d'un cas de force majeure "
        "(catastrophe naturelle, coupure générale d'électricité ou d'internet, décision gouvernementale, etc.).",
        S["corps"]
    ))
    story.append(sp(2))

    # ══════════════════════════════════════════════════════════════
    # ARTICLE 11 — DROIT APPLICABLE ET LITIGES
    # ══════════════════════════════════════════════════════════════
    story.append(bandeau_section("ARTICLE 11 — DROIT APPLICABLE ET RÈGLEMENT DES LITIGES", S))
    story.append(sp(1))
    story.append(Paragraph(
        "Le présent contrat est soumis au droit ivoirien. En cas de litige, les parties s'engagent à rechercher "
        "une solution amiable dans un délai de <b>30 jours</b> à compter de la notification du différend. "
        "À défaut d'accord amiable, les parties attribuent compétence exclusive aux juridictions compétentes "
        "d'Abidjan (République de Côte d'Ivoire).",
        S["corps"]
    ))
    story.append(sp(2))

    # ══════════════════════════════════════════════════════════════
    # SIGNATURES
    # ══════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(bandeau_section("SIGNATURES DES PARTIES", S))
    story.append(sp(2))

    story.append(Paragraph(
        "Les soussignés reconnaissent avoir pris connaissance de l'intégralité des dispositions du présent contrat "
        "et en acceptent les termes sans réserve.",
        S["corps"]
    ))
    story.append(sp(1))
    story.append(Paragraph(
        f"Fait à Abidjan, le ______________________________",
        ParagraphStyle("fact", fontName="Helvetica", fontSize=10, textColor=GRIS_TEXTE, alignment=TA_CENTER)
    ))
    story.append(sp(2))

    sign_data = [
        [
            Paragraph("LE PRESTATAIRE", S["signature_label"]),
            Paragraph("LE CLIENT", S["signature_label"]),
        ],
        [
            Paragraph(
                f"<b>{PRESTATAIRE['nom']}</b><br/><br/>"
                "Nom & Prénom : ________________________<br/><br/>"
                "Qualité : ________________________<br/><br/>"
                "Signature et cachet :",
                S["signature_champ"]
            ),
            Paragraph(
                f"<b>Raison sociale : {CLIENT['raison']}</b><br/><br/>"
                "Nom & Prénom : ________________________<br/><br/>"
                "Qualité : ________________________<br/><br/>"
                "Signature et cachet :",
                S["signature_champ"]
            ),
        ],
        [
            Paragraph(" " * 60 + "\n" * 6, ParagraphStyle("szone", fontName="Helvetica", fontSize=9)),
            Paragraph(" " * 60 + "\n" * 6, ParagraphStyle("szone", fontName="Helvetica", fontSize=9)),
        ],
    ]
    sw = (W - 30*mm) / 2
    sign_t = Table(sign_data, colWidths=[sw, sw])
    sign_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BLEU_CLAIR),
        ("GRID",          (0, 0), (-1, -1), 0.5, GRIS_BORDURE),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE",     (0, 0), (-1, 0), 2, BLEU_FONCE),
        ("LINEBELOW",     (0, -1), (-1, -1), 2, ORANGE),
        ("ROWHEIGHT",     (0, 2), (-1, 2), 35*mm),
    ]))
    story.append(sign_t)
    story.append(sp(2))

    # Note finale
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS_BORDURE))
    story.append(sp(1))
    story.append(Paragraph(
        f"Document établi en deux (2) exemplaires originaux — un pour chaque partie. "
        f"Réf. {REF_CONTRAT} — {PRESTATAIRE['nom']} — {PRESTATAIRE['email']}",
        ParagraphStyle("fn", fontName="Helvetica-Oblique", fontSize=8, textColor=colors.HexColor("#888888"), alignment=TA_CENTER)
    ))

    # ══════════════════════════════════════════════════════════════
    # CONSTRUCTION
    # ══════════════════════════════════════════════════════════════
    doc.build(story, canvasmaker=PageCanvas)
    print(f"\n✅  Contrat généré : {OUTPUT_FILE}")
    print(f"    Taille : {os.path.getsize(OUTPUT_FILE) / 1024:.1f} Ko")


if __name__ == "__main__":
    build_pdf()
