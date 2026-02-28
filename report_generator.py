from fpdf import FPDF
from datetime import datetime
import io


class WellnessReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(102, 126, 234)
        self.cell(0, 15, "MindCare AI - Wellness Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(102, 126, 234)
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Generated on {datetime.now().strftime('%d %B %Y, %I:%M %p')} | Page {self.page_no()}", align="C")


def generate_report(username: str, sessions: list) -> bytes:
    """Generate a PDF wellness report and return bytes."""
    pdf = WellnessReport()
    pdf.add_page()

    # ── User Info ──
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 8, f"Patient: {username}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Report Date: {datetime.now().strftime('%d %B %Y')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Total Sessions: {len(sessions)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    if not sessions:
        pdf.set_font("Helvetica", "I", 12)
        pdf.cell(0, 10, "No sessions recorded yet. Start chatting to build your wellness profile.", new_x="LMARGIN", new_y="NEXT")
        return pdf.output()

    # ── Calculate Stats ──
    stress_scores = [s["stress_score"] for s in sessions]
    anxiety_scores = [s["anxiety_score"] for s in sessions]
    mood_labels = [s["mood_label"] for s in sessions]

    avg_stress = sum(stress_scores) / len(stress_scores)
    avg_anxiety = sum(anxiety_scores) / len(anxiety_scores)
    max_stress = max(stress_scores)
    max_anxiety = max(anxiety_scores)

    # Mood distribution
    mood_counts = {}
    for m in mood_labels:
        mood_counts[m] = mood_counts.get(m, 0) + 1

    # ── Summary Section ──
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(102, 126, 234)
    pdf.cell(0, 10, "Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)

    pdf.cell(95, 8, f"Average Stress Level: {avg_stress:.1f} / 10", border=1)
    pdf.cell(95, 8, f"Average Anxiety Level: {avg_anxiety:.1f} / 10", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(95, 8, f"Highest Stress: {max_stress} / 10", border=1)
    pdf.cell(95, 8, f"Highest Anxiety: {max_anxiety} / 10", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # ── Stress Level Interpretation ──
    pdf.set_font("Helvetica", "B", 12)
    if avg_stress <= 3:
        level_text = "Low Stress - You are managing well!"
        pdf.set_text_color(34, 197, 94)
    elif avg_stress <= 6:
        level_text = "Moderate Stress - Consider self-care practices"
        pdf.set_text_color(234, 179, 8)
    else:
        level_text = "High Stress - Professional support recommended"
        pdf.set_text_color(239, 68, 68)
    pdf.cell(0, 8, level_text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(50, 50, 50)
    pdf.ln(3)

    # ── Mood Distribution ──
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(102, 126, 234)
    pdf.cell(0, 10, "Mood Distribution", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)

    for mood, count in sorted(mood_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(sessions)) * 100
        bar_width = pct * 1.2
        pdf.cell(30, 7, mood.capitalize())
        # Draw bar
        pdf.set_fill_color(102, 126, 234)
        pdf.cell(bar_width, 7, "", fill=True)
        pdf.cell(30, 7, f"  {count} ({pct:.0f}%)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # ── Session Details Table ──
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(102, 126, 234)
    pdf.cell(0, 10, "Session History", new_x="LMARGIN", new_y="NEXT")

    # Table header
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(102, 126, 234)
    pdf.cell(35, 8, "Date/Time", border=1, fill=True)
    pdf.cell(70, 8, "Your Message", border=1, fill=True)
    pdf.cell(25, 8, "Stress", border=1, fill=True, align="C")
    pdf.cell(25, 8, "Anxiety", border=1, fill=True, align="C")
    pdf.cell(30, 8, "Mood", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

    # Table rows (last 30 sessions)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(50, 50, 50)
    for s in sessions[-30:]:
        # Parse and format timestamp
        try:
            ts = datetime.fromisoformat(s["timestamp"]).strftime("%d/%m %H:%M")
        except:
            ts = s["timestamp"][:16]

        msg = s["user_message"][:45] + ("..." if len(s["user_message"]) > 45 else "")

        pdf.cell(35, 7, ts, border=1)
        pdf.cell(70, 7, msg, border=1)
        pdf.cell(25, 7, str(s["stress_score"]), border=1, align="C")
        pdf.cell(25, 7, str(s["anxiety_score"]), border=1, align="C")
        pdf.cell(30, 7, s["mood_label"].capitalize(), border=1, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # ── Recommendations ──
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(102, 126, 234)
    pdf.cell(0, 10, "Wellness Recommendations", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)

    recommendations = []
    if avg_stress > 5:
        recommendations.append("- Practice deep breathing exercises (box breathing: 4s inhale, 4s hold, 4s exhale, 4s hold)")
        recommendations.append("- Consider scheduling regular breaks during work/study")
        recommendations.append("- Try progressive muscle relaxation before bed")
    if avg_anxiety > 5:
        recommendations.append("- Use the 5-4-3-2-1 grounding technique when feeling anxious")
        recommendations.append("- Limit caffeine and sugar intake")
        recommendations.append("- Consider speaking with a mental health professional")
    if avg_stress <= 5 and avg_anxiety <= 5:
        recommendations.append("- Your stress and anxiety levels look manageable - keep up the good self-care!")
        recommendations.append("- Continue maintaining healthy sleep habits (7-8 hours)")
        recommendations.append("- Stay connected with friends and family")

    recommendations.append("- Journal your thoughts daily for 5-10 minutes")
    recommendations.append("- Exercise for at least 30 minutes, 3 times a week")

    for rec in recommendations:
        pdf.cell(0, 7, rec, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 7, "Disclaimer: This report is AI-generated and not a substitute for professional medical advice.", new_x="LMARGIN", new_y="NEXT")

    return pdf.output()
