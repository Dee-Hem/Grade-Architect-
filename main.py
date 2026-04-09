
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle
from fpdf import FPDF
import json
import os

# --- PREMIUM STYLED COMPONENTS ---

class StyledInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.12, 0.18, 0.3, 1) # Navy-tinted "Glass" look
        self.foreground_color = (1, 1, 1, 1)
        self.cursor_color = (0.83, 0.68, 0.21, 1) # Gold
        self.font_size = '16sp'
        self.padding = [15, 12, 15, 12]
        self.hint_text_color = (0.5, 0.5, 0.6, 1)
        self.multiline = False

class ExecutiveButton(Button):
    def __init__(self, hex_color='#d4af37', **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0) # Managed by canvas
        self.color = (1, 1, 1, 1)
        self.bold = True
        self.font_size = '14sp'
        self.hex = hex_color
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(rgb=get_color_from_hex(self.hex))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10,])

class GradeArchitect(App):
    def build(self):
        # --- BRANDING ---
        self.icon = 'icon.png'
        
        self.data_file = 'records.json'
        self.records = self.load_data()
        self.grade_points = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1, 'F': 0}
        self.colors = {'A':(46,204,113), 'B':(52,152,219), 'C':(241,196,15), 'D':(230,126,34), 'E':(231,76,60), 'F':(149,165,166)}

        # Main Root Layout
        root = BoxLayout(orientation='vertical', padding=20, spacing=15)
        with root.canvas.before:
            Color(rgb=get_color_from_hex('#0f172a')) # Global Deep Navy
            self.rect = RoundedRectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_rect, size=self._update_rect)

        # --- HEADER: THE PROFILE STACK ---
        prof = BoxLayout(orientation='vertical', size_hint_y=None, height='140dp', spacing=8)
        self.name_in = StyledInput(hint_text="Student Name")
        self.dept_in = StyledInput(hint_text="Department")
        self.level_in = StyledInput(hint_text="Level")
        prof.add_widget(self.name_in); prof.add_widget(self.dept_in); prof.add_widget(self.level_in)
        root.add_widget(prof)

        # --- DASHBOARD: THE HERO CARD ---
        dash_card = BoxLayout(orientation='vertical', size_hint_y=None, height='130dp', padding=[0, 10])
        with dash_card.canvas.before:
            Color(rgb=get_color_from_hex('#1e293b')) # Elevated Navy Card
            self.card_rect = RoundedRectangle(pos=dash_card.pos, size=dash_card.size, radius=[20,])
        dash_card.bind(pos=self._update_card, size=self._update_card)

        self.cgpa_label = Label(text="0.00", font_size='64sp', bold=True, color=get_color_from_hex('#d4af37'))
        self.honor_label = Label(text="CLASS: -", font_size='12sp', color=(0.8, 0.8, 0.8, 1), bold=True)
        dash_card.add_widget(self.cgpa_label); dash_card.add_widget(self.honor_label)
        root.add_widget(dash_card)

        # --- COURSE ENTRY ---
        inputs = GridLayout(cols=2, size_hint_y=None, height='90dp', spacing=10)
        self.sem_in = StyledInput(hint_text="Sem (300L Rain)")
        self.course_in = StyledInput(hint_text="Code")
        self.unit_in = StyledInput(hint_text="Units", input_filter='int')
        self.grade_in = StyledInput(hint_text="Grade (A-F)")
        inputs.add_widget(self.sem_in); inputs.add_widget(self.course_in)
        inputs.add_widget(self.unit_in); inputs.add_widget(self.grade_in)
        root.add_widget(inputs)

        # --- CONTROLS: REFINED BUTTON GRID ---
        btns = GridLayout(cols=3, size_hint_y=None, height='120dp', spacing=10)
        btn_config = [
            ("ADD", '#10b981', self.add_course), ("UNDO", '#f59e0b', self.undo_last), ("RESET", '#ef4444', self.clear_all),
            ("JSON", '#6366f1', self.export_json), ("IMPORT", '#06b6d4', self.import_json), ("PDF", '#d4af37', self.export_pdf)
        ]

        for text, color, func in btn_config:
            b = ExecutiveButton(text=text, hex_color=color)
            b.bind(on_press=func)
            btns.add_widget(b)
        root.add_widget(btns)

        # --- SCROLL VIEW: COURSE LIST ---
        self.scroll = ScrollView(bar_width=4, bar_color=get_color_from_hex('#d4af37'))
        self.display_label = Label(text="", size_hint_y=None, halign='left', valign='top', markup=True, padding=(15,15), font_size='15sp')
        self.display_label.bind(texture_size=self.display_label.setter('size'))
        self.scroll.add_widget(self.display_label); root.add_widget(self.scroll)

        self.refresh_ui()
        return root

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _update_card(self, instance, value):
        self.card_rect.pos = instance.pos
        self.card_rect.size = instance.size

    def get_honors(self, cgpa):
        if cgpa >= 4.50: return "FIRST CLASS"
        elif cgpa >= 3.50: return "SECOND CLASS (UPPER)"
        elif cgpa >= 2.40: return "SECOND CLASS (LOWER)"
        elif cgpa >= 1.50: return "THIRD CLASS"
        return "PASS"

    def refresh_ui(self):
        if not self.records:
            self.cgpa_label.text = "0.00"; self.honor_label.text = "CLASS: -"; self.display_label.text = "Waiting for records..."; return
        pts_t, units_t = 0, 0
        txt = ""
        for r in self.records:
            u, g = r['units'], r['grade']
            p = self.grade_points.get(g, 0)
            pts_t += (p * u); units_t += u
            txt += f"[color=d4af37][b]{r['sem']}[/b][/color] | {r['name']} | [b]{g}[/b] ({u}U)
"
        cgpa = pts_t / units_t if units_t > 0 else 0
        self.cgpa_label.text = "{:.2f}".format(cgpa)
        self.honor_label.text = "CLASS: " + self.get_honors(cgpa)
        self.display_label.text = txt

    def add_course(self, *args):
        if all([self.sem_in.text, self.course_in.text, self.unit_in.text, self.grade_in.text]):
            self.records.append({'sem': self.sem_in.text, 'name': self.course_in.text.upper(), 'units': int(self.unit_in.text), 'grade': self.grade_in.text.upper()})
            self.save_data(); self.refresh_ui(); self.course_in.text = ""; self.unit_in.text = ""; self.grade_in.text = ""

    def undo_last(self, *args):
        if self.records: self.records.pop(); self.save_data(); self.refresh_ui()

    def clear_all(self, *args):
        self.records = []; self.save_data(); self.refresh_ui()

    def export_pdf(self, *args):
        if not self.records: return
        pdf = FPDF()
        pdf.add_page(); pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "OFFICIAL GRADE ARCHITECT REPORT", ln=1, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 7, f"Name: {self.name_in.text}", ln=1)
        pdf.cell(0, 7, f"Department: {self.dept_in.text}", ln=1)
        pdf.cell(0, 7, f"Level: {self.level_in.text}", ln=1)

        grouped = {}
        for r in self.records: grouped.setdefault(r['sem'], []).append(r)

        for sem, courses in grouped.items():
            pdf.ln(5); pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 10, " Semester: " + sem, 1, ln=1, fill=True)
            s_pts, s_u = 0, 0
            for c in courses:
                pdf.set_font("Arial", '', 10); pdf.cell(100, 8, " " + c['name'], 1); pdf.cell(40, 8, " Units: " + str(c['units']), 1)
                rgb = self.colors.get(c['grade'], (0,0,0)); pdf.set_text_color(*rgb)
                pdf.cell(40, 8, " Grade: " + c['grade'], 1); pdf.set_text_color(0,0,0); pdf.ln()
                s_pts += (self.grade_points.get(c['grade'],0) * c['units']); s_u += c['units']
            pdf.set_font("Arial", 'I', 9); pdf.cell(0, 7, f"GPA: {s_pts/s_u if s_u>0 else 0:.2f}  ", 0, ln=1, align='R')

        pdf.ln(10); pdf.set_font("Arial", 'B', 14); 
        # Correctly parsing the float from the cleaned label
        final_cgpa = float(self.cgpa_label.text)
        pdf.cell(0, 12, f"CUMULATIVE CGPA: {final_cgpa:.2f}", 1, ln=1, align='C')
        pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, f"HONORS: {self.get_honors(final_cgpa)}", 0, ln=1, align='C')

        try: 
            save_path = "/storage/emulated/0/Download/GradeArchitect_Report.pdf"
            pdf.output(save_path); self.cgpa_label.text = "SAVED TO DOWNLOADS"
        except: 
            pdf.output("Report.pdf"); self.cgpa_label.text = "SAVED LOCALLY"

    def export_json(self, *args):
        try:
            with open("/storage/emulated/0/Download/GradeArchitect_Backup.json", 'w') as f: json.dump(self.records, f)
            self.cgpa_label.text = "BACKUP CREATED"
        except: self.cgpa_label.text = "EXPORT FAILED"

    def import_json(self, *args):
        try:
            with open("/storage/emulated/0/Download/GradeArchitect_Backup.json", 'r') as f: self.records = json.load(f)
            self.save_data(); self.refresh_ui(); self.cgpa_label.text = "RECORDS IMPORTED"
        except: self.cgpa_label.text = "FILE NOT FOUND"

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f: return json.load(f)
        return []
    def save_data(self):
        with open(self.data_file, 'w') as f: json.dump(self.records, f)

if __name__ == '__main__':
    GradeArchitect().run()
