import os
import json
import sys
import traceback
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.utils import get_color_from_hex, platform
from kivy.graphics import Color, RoundedRectangle

# --- 1. EMERGENCY LOGGING (Saves to your Downloads folder if it crashes) ---
if platform == 'android':
    try:
        log_path = "/storage/emulated/0/Download/grade_architect_error.txt"
        sys.stderr = open(log_path, "w")
        sys.stdout = sys.stderr
    except:
        pass

# Try-Except on FPDF to prevent total crash if the recipe fails
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- 2. PREMIUM STYLED COMPONENTS ---

class StyledInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.12, 0.18, 0.3, 1) 
        self.foreground_color = (1, 1, 1, 1)
        self.cursor_color = (0.83, 0.68, 0.21, 1) 
        self.font_size = '16sp'
        self.padding = [15, 12, 15, 12]
        self.hint_text_color = (0.5, 0.5, 0.6, 1)
        self.multiline = False

class ExecutiveButton(Button):
    def __init__(self, hex_color='#d4af37', **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0) 
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
        # Configuration
        self.icon = 'icon.png'
        self.grade_points = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1, 'F': 0}
        self.colors = {'A':(46,204,113), 'B':(52,152,219), 'C':(241,196,15), 'D':(230,126,34), 'E':(231,76,60), 'F':(149,165,166)}

        # Load records after app is initialized
        self.records = self.load_data()

        # Main Root Layout
        root = BoxLayout(orientation='vertical', padding=20, spacing=15)
        with root.canvas.before:
            Color(rgb=get_color_from_hex('#0f172a')) 
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
            Color(rgb=get_color_from_hex('#1e293b')) 
            self.card_rect = RoundedRectangle(pos=dash_card.pos, size=dash_card.size, radius=[20,])
        dash_card.bind(pos=self._update_card, size=self._update_card)

        self.cgpa_label = Label(text="0.00", font_size='64sp', bold=True, color=get_color_from_hex('#d4af37'))
        self.honor_label = Label(text="CLASS: -", font_size='12sp', color=(0.8, 0.8, 0.8, 1), bold=True)
        dash_card.add_widget(self.cgpa_label); dash_card.add_widget(self.honor_label)
        root.add_widget(dash_card)

        # --- COURSE ENTRY ---
        inputs = GridLayout(cols=2, size_hint_y=None, height='90dp', spacing=10)
        self.sem_in = StyledInput(hint_text="Sem (e.g., 300L Rain)")
        self.course_in = StyledInput(hint_text="Code")
        self.unit_in = StyledInput(hint_text="Units", input_filter='int')
        self.grade_in = StyledInput(hint_text="Grade (A-F)")
        inputs.add_widget(self.sem_in); inputs.add_widget(self.course_in)
        inputs.add_widget(self.unit_in); inputs.add_widget(self.grade_in)
        root.add_widget(inputs)

        # --- CONTROLS ---
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

        # --- SCROLL VIEW ---
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

    def load_data(self):
        # Correct path for Android Sandbox
        path = os.path.join(self.user_data_dir, 'records.json')
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_data(self):
        path = os.path.join(self.user_data_dir, 'records.json')
        try:
            with open(path, 'w') as f:
                json.dump(self.records, f)
        except:
            pass

    def refresh_ui(self):
        if not self.records:
            self.cgpa_label.text = "0.00"; self.honor_label.text = "CLASS: -"; self.display_label.text = "Waiting for records..."
            return
        
        pts_t, units_t = 0, 0
        txt = ""
        for r in self.records:
            u = r.get('units', 0)
            g = r.get('grade', 'F')
            p = self.grade_points.get(g, 0)
            pts_t += (p * u); units_t += u
            txt += f"[color=d4af37][b]{r.get('sem','?')}[/b][/color] | {r.get('name','?')} | [b]{g}[/b] ({u}U)\n"
        
        cgpa = pts_t / units_t if units_t > 0 else 0
        self.cgpa_label.text = "{:.2f}".format(cgpa)
        self.honor_label.text = "CLASS: " + self.get_honors(cgpa)
        self.display_label.text = txt

    def add_course(self, *args):
        if all([self.sem_in.text, self.course_in.text, self.unit_in.text, self.grade_in.text]):
            try:
                self.records.append({
                    'sem': self.sem_in.text, 
                    'name': self.course_in.text.upper(), 
                    'units': int(self.unit_in.text), 
                    'grade': self.grade_in.text.upper()
                })
                self.save_data(); self.refresh_ui()
                self.course_in.text = ""; self.unit_in.text = ""; self.grade_in.text = ""
            except:
                pass

    def undo_last(self, *args):
        if self.records: self.records.pop(); self.save_data(); self.refresh_ui()

    def clear_all(self, *args):
        self.records = []; self.save_data(); self.refresh_ui()

    def export_pdf(self, *args):
        if not self.records or not FPDF: return
        try:
            pdf = FPDF()
            pdf.add_page(); pdf.set_font("helvetica", 'B', 16) # Helvetica is safe for Android
            pdf.cell(200, 10, "OFFICIAL GRADE ARCHITECT REPORT", ln=1, align='C')
            
            pdf.set_font("helvetica", '', 10)
            pdf.cell(0, 7, f"Name: {self.name_in.text}", ln=1)
            pdf.cell(0, 7, f"Dept: {self.dept_in.text} | Level: {self.level_in.text}", ln=1)

            for r in self.records:
                pdf.cell(0, 8, f"{r['sem']} | {r['name']} | Units: {r['units']} | Grade: {r['grade']}", ln=1)

            final_cgpa = float(self.cgpa_label.text)
            pdf.ln(10); pdf.set_font("helvetica", 'B', 14)
            pdf.cell(0, 12, f"CGPA: {final_cgpa:.2f} | {self.get_honors(final_cgpa)}", 1, ln=1, align='C')

            save_path = "/storage/emulated/0/Download/GradeArchitect_Report.pdf"
            pdf.output(save_path)
            self.cgpa_label.text = "PDF READY"
        except Exception as e:
            self.cgpa_label.text = "PDF ERROR"
            print(f"PDF Error: {e}")

    def export_json(self, *args):
        try:
            path = "/storage/emulated/0/Download/GradeArchitect_Backup.json"
            with open(path, 'w') as f: json.dump(self.records, f)
            self.cgpa_label.text = "JSON READY"
        except: self.cgpa_label.text = "SAVE FAILED"

    def import_json(self, *args):
        try:
            path = "/storage/emulated/0/Download/GradeArchitect_Backup.json"
            with open(path, 'r') as f: self.records = json.load(f)
            self.save_data(); self.refresh_ui(); self.cgpa_label.text = "IMPORTED"
        except: self.cgpa_label.text = "NOT FOUND"

if __name__ == '__main__':
    try:
        GradeArchitect().run()
    except Exception:
        traceback.print_exc()
