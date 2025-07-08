"""
GUI Screens Module - Premium UI Components
Defines all screens for the AI EPUB Rewriter application
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.uix.effectwidget import EffectWidget
from kivy.uix.modalview import ModalView
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.app import App

import json
from pathlib import Path
from core.project_manager import ProjectManager
from datetime import datetime


class GlassPanel(FloatLayout):
    """Base class for glassmorphic panels"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.update_graphics, pos=self.update_graphics)
        Clock.schedule_once(self.update_graphics, 0)
        
    def update_graphics(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Semi-transparent background with blur effect
            Color(0.1, 0.1, 0.1, 0.85)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(20)]
            )
            # Border for glass effect
            Color(0.784, 0.608, 0.235, 0.3)  # Gold accent with transparency
            self.border = Line(
                rounded_rectangle=(
                    self.x, self.y, self.width, self.height, dp(20)
                ),
                width=dp(1.5)
            )


class AnimatedButton(Button):
    """Premium animated button with hover effects"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)  # Transparent background
        self.bind(on_enter=self.on_hover, on_leave=self.on_leave)
        self.bind(size=self.update_graphics, pos=self.update_graphics)
        Clock.schedule_once(self.setup_graphics, 0)
        
    def setup_graphics(self, dt):
        self.canvas.before.clear()
        with self.canvas.before:
            # Default state - subtle gold
            self.bg_color = Color(0.784, 0.608, 0.235, 0.2)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(15)]
            )
            # Border
            self.border_color = Color(0.784, 0.608, 0.235, 0.8)
            self.border = Line(
                rounded_rectangle=(
                    self.x, self.y, self.width, self.height, dp(15)
                ),
                width=dp(2)
            )
    
    def update_graphics(self, *args):
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size
            self.border.rounded_rectangle = (
                self.x, self.y, self.width, self.height, dp(15)
            )
    
    def on_hover(self, *args):
        # Animate to brighter gold on hover
        if hasattr(self, 'bg_color'):
            Animation(rgba=(0.784, 0.608, 0.235, 0.4), duration=0.2).start(self.bg_color)
    
    def on_leave(self, *args):
        # Animate back to default
        if hasattr(self, 'bg_color'):
            Animation(rgba=(0.784, 0.608, 0.235, 0.2), duration=0.2).start(self.bg_color)


class HomeScreen(Screen):
    """Welcome screen with brand presentation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.setup_ui, 0)
    
    def setup_ui(self, dt):
        # Main layout
        layout = FloatLayout()
        
        # Central glass panel
        panel = GlassPanel(
            size_hint=(0.6, 0.7),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        # Content layout
        content = BoxLayout(
            orientation='vertical',
            padding=dp(60),
            spacing=dp(30)
        )
        
        # Title with premium typography
        title = Label(
            text='[font=assets/fonts/premium-serif.ttf]AI EPUB[/font]\n[size=36]Rewriter[/size]',
            font_size=dp(72),
            color=(0.941, 0.902, 0.824, 1),  # Creamy gold
            markup=True,
            halign='center'
        )
        
        # Subtitle
        subtitle = Label(
            text='Transform your EPUBs with cinematic AI-powered rewriting',
            font_size=dp(18),
            color=(0.8, 0.8, 0.8, 0.9),
            halign='center'
        )
        
        # Animated gradient line
        self.create_animated_line(content)
        
        # Action buttons
        btn_layout = BoxLayout(
            orientation='horizontal',
            spacing=dp(20),
            size_hint_y=None,
            height=dp(60)
        )
        
        new_project_btn = AnimatedButton(
            text='Create New Project',
            font_size=dp(16),
            color=(0.941, 0.902, 0.824, 1)
        )
        new_project_btn.bind(on_release=self.go_to_new_project)
        
        browse_btn = AnimatedButton(
            text='Browse Projects',
            font_size=dp(16),
            color=(0.941, 0.902, 0.824, 1)
        )
        browse_btn.bind(on_release=self.go_to_projects)
        
        btn_layout.add_widget(new_project_btn)
        btn_layout.add_widget(browse_btn)
        
        # Assemble content
        content.add_widget(title)
        content.add_widget(subtitle)
        content.add_widget(Label(size_hint_y=0.3))  # Spacer
        content.add_widget(btn_layout)
        
        panel.add_widget(content)
        layout.add_widget(panel)
        
        self.add_widget(layout)
    
    def create_animated_line(self, parent):
        """Create an animated decorative line"""
        from kivy.uix.widget import Widget
        
        class AnimatedLine(Widget):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.size_hint_y = None
                self.height = dp(4)
                Clock.schedule_interval(self.update_line, 1/60.)
                self.time = 0
                
            def update_line(self, dt):
                self.time += dt
                self.canvas.clear()
                with self.canvas:
                    # Animated gradient effect
                    import math
                    offset = math.sin(self.time * 2) * 0.5 + 0.5
                    Color(0.784, 0.608, 0.235, offset)
                    Line(
                        points=[self.x, self.center_y, self.right, self.center_y],
                        width=dp(2)
                    )
        
        parent.add_widget(AnimatedLine())
    
    def go_to_new_project(self, instance):
        self.manager.current = 'new_project'
    
    def go_to_projects(self, instance):
        self.manager.current = 'projects'


class ProjectsScreen(Screen):
    """Project management screen"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.setup_ui, 0)
    
    def setup_ui(self, dt):
        layout = FloatLayout()
        
        # Header panel
        header = GlassPanel(
            size_hint=(0.9, 0.15),
            pos_hint={'center_x': 0.5, 'top': 0.95}
        )
        
        header_content = BoxLayout(
            orientation='horizontal',
            padding=dp(30),
            spacing=dp(20)
        )
        
        # Back button
        back_btn = AnimatedButton(
            text='← Back',
            size_hint_x=None,
            width=dp(120),
            font_size=dp(16),
            color=(0.941, 0.902, 0.824, 1)
        )
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        
        # Title
        title = Label(
            text='Your Projects',
            font_size=dp(36),
            color=(0.941, 0.902, 0.824, 1)
        )
        
        header_content.add_widget(back_btn)
        header_content.add_widget(title)
        header.add_widget(header_content)
        
        # Projects list panel
        list_panel = GlassPanel(
            size_hint=(0.9, 0.75),
            pos_hint={'center_x': 0.5, 'top': 0.78}
        )
        
        # Scrollable project list
        scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(10),
            bar_color=(0.784, 0.608, 0.235, 0.5),
            bar_inactive_color=(0.784, 0.608, 0.235, 0.2)
        )
        
        self.projects_container = BoxLayout(
            orientation='vertical',
            spacing=dp(10),
            padding=dp(20),
            size_hint_y=None
        )
        self.projects_container.bind(minimum_height=self.projects_container.setter('height'))
        
        scroll.add_widget(self.projects_container)
        list_panel.add_widget(scroll)
        
        layout.add_widget(header)
        layout.add_widget(list_panel)
        
        self.add_widget(layout)
        
        # Load projects
        Clock.schedule_once(self.load_projects, 0.1)
    
    def load_projects(self, dt):
        app = App.get_running_app()
        app.load_projects()
        
        self.projects_container.clear_widgets()
        
        for project_name in app.projects_list:
            self.add_project_item(project_name)
    
    def add_project_item(self, project_name):
        """Create a premium project item widget"""
        item = GlassPanel(size_hint_y=None, height=dp(100))
        
        item_layout = BoxLayout(
            orientation='horizontal',
            padding=dp(20),
            spacing=dp(20)
        )
        
        # Project info
        info_layout = BoxLayout(orientation='vertical', spacing=dp(5))
        
        name_label = Label(
            text=project_name,
            font_size=dp(20),
            color=(0.941, 0.902, 0.824, 1),
            halign='left'
        )
        
        # Load project status
        try:
            project = ProjectManager(project_name)
            state_path = Path(project.project_dir) / 'project_state.json'
            with open(state_path) as f:
                state = json.load(f)
            
            total = len(state['chapters'])
            completed = sum(1 for c in state['chapters'].values() if c['status'] == 'completed')
            
            status_label = Label(
                text=f'Progress: {completed}/{total} chapters',
                font_size=dp(14),
                color=(0.7, 0.7, 0.7, 0.9),
                halign='left'
            )
        except:
            status_label = Label(
                text='Status: Unknown',
                font_size=dp(14),
                color=(0.7, 0.7, 0.7, 0.9),
                halign='left'
            )
        
        info_layout.add_widget(name_label)
        info_layout.add_widget(status_label)
        
        # Action buttons
        btn_layout = BoxLayout(
            orientation='horizontal',
            spacing=dp(10),
            size_hint_x=None,
            width=dp(300)
        )
        
        open_btn = AnimatedButton(
            text='Open',
            font_size=dp(14),
            color=(0.941, 0.902, 0.824, 1)
        )
        open_btn.bind(on_release=lambda x: self.open_project(project_name))
        
        delete_btn = AnimatedButton(
            text='Delete',
            font_size=dp(14),
            color=(0.941, 0.902, 0.824, 1)
        )
        
        btn_layout.add_widget(open_btn)
        btn_layout.add_widget(delete_btn)
        
        item_layout.add_widget(info_layout)
        item_layout.add_widget(btn_layout)
        
        item.add_widget(item_layout)
        self.projects_container.add_widget(item)
    
    def open_project(self, project_name):
        app = App.get_running_app()
        app.current_project = project_name
        self.manager.current = 'processing'


class NewProjectScreen(Screen):
    """Screen for creating new projects"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.setup_ui, 0)
    
    def setup_ui(self, dt):
        layout = FloatLayout()
        
        # Main panel
        panel = GlassPanel(
            size_hint=(0.8, 0.85),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        content = BoxLayout(
            orientation='vertical',
            padding=dp(40),
            spacing=dp(20)
        )
        
        # Header
        header = BoxLayout(
            size_hint_y=None,
            height=dp(60),
            spacing=dp(20)
        )
        
        back_btn = AnimatedButton(
            text='← Back',
            size_hint_x=None,
            width=dp(120),
            font_size=dp(16),
            color=(0.941, 0.902, 0.824, 1)
        )
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        
        title = Label(
            text='Create New Project',
            font_size=dp(32),
            color=(0.941, 0.902, 0.824, 1)
        )
        
        header.add_widget(back_btn)
        header.add_widget(title)
        
        # Form fields
        form_layout = BoxLayout(
            orientation='vertical',
            spacing=dp(20),
            size_hint_y=0.7
        )
        
        # Project name input
        self.name_input = self.create_form_field(
            'Project Name',
            'Enter a unique name for your project'
        )
        
        # EPUB file selector
        self.epub_path_label = Label(
            text='No EPUB selected',
            size_hint_y=None,
            height=dp(30),
            color=(0.7, 0.7, 0.7, 0.9)
        )
        
        epub_btn = AnimatedButton(
            text='Select EPUB File',
            size_hint_y=None,
            height=dp(50),
            font_size=dp(16),
            color=(0.941, 0.902, 0.824, 1)
        )
        epub_btn.bind(on_release=self.select_epub_file)
        
        # Style reference selector
        self.style_path_label = Label(
            text='No style reference selected',
            size_hint_y=None,
            height=dp(30),
            color=(0.7, 0.7, 0.7, 0.9)
        )
        
        style_btn = AnimatedButton(
            text='Select Style Reference',
            size_hint_y=None,
            height=dp(50),
            font_size=dp(16),
            color=(0.941, 0.902, 0.824, 1)
        )
        style_btn.bind(on_release=self.select_style_file)
        
        form_layout.add_widget(self.name_input)
        form_layout.add_widget(Label(text='EPUB File:', size_hint_y=None, height=dp(30), color=(0.8, 0.8, 0.8, 1)))
        form_layout.add_widget(self.epub_path_label)
        form_layout.add_widget(epub_btn)
        form_layout.add_widget(Label(text='Style Reference:', size_hint_y=None, height=dp(30), color=(0.8, 0.8, 0.8, 1)))
        form_layout.add_widget(self.style_path_label)
        form_layout.add_widget(style_btn)
        
        # Create button
        create_btn = AnimatedButton(
            text='Create Project',
            size_hint=(None, None),
            size=(dp(200), dp(60)),
            pos_hint={'center_x': 0.5},
            font_size=dp(18),
            color=(0.941, 0.902, 0.824, 1)
        )
        create_btn.bind(on_release=self.create_project)
        
        content.add_widget(header)
        content.add_widget(form_layout)
        content.add_widget(create_btn)
        
        panel.add_widget(content)
        layout.add_widget(panel)
        
        self.add_widget(layout)
        
        self.epub_path = ''
        self.style_path = ''
    
    def create_form_field(self, label_text, hint_text):
        """Create a premium form field"""
        layout = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None, height=dp(80))
        
        label = Label(
            text=label_text,
            size_hint_y=None,
            height=dp(25),
            color=(0.8, 0.8, 0.8, 1),
            halign='left'
        )
        
        text_input = TextInput(
            hint_text=hint_text,
            multiline=False,
            size_hint_y=None,
            height=dp(45),
            font_size=dp(16),
            background_color=(0.1, 0.1, 0.1, 0.7),
            foreground_color=(0.941, 0.902, 0.824, 1),
            cursor_color=(0.784, 0.608, 0.235, 1),
            padding=[dp(15), dp(10)]
        )
        
        layout.add_widget(label)
        layout.add_widget(text_input)
        
        return text_input
    
    def select_epub_file(self, instance):
        self.show_file_chooser('epub')
    
    def select_style_file(self, instance):
        self.show_file_chooser('style')
    
    def show_file_chooser(self, file_type):
        """Show premium file chooser dialog"""
        modal = ModalView(
            size_hint=(0.8, 0.8),
            background_color=(0, 0, 0, 0.8)
        )
        
        panel = GlassPanel()
        
        layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(10)
        )
        
        # Title
        title = Label(
            text=f'Select {file_type.upper()} File',
            size_hint_y=None,
            height=dp(40),
            font_size=dp(24),
            color=(0.941, 0.902, 0.824, 1)
        )
        
        # File chooser
        file_chooser = FileChooserListView(
            filters=['*.epub'] if file_type == 'epub' else ['*.txt'],
            size_hint_y=0.8
        )
        
        # Buttons
        btn_layout = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )
        
        select_btn = AnimatedButton(
            text='Select',
            font_size=dp(16),
            color=(0.941, 0.902, 0.824, 1)
        )
        
        cancel_btn = AnimatedButton(
            text='Cancel',
            font_size=dp(16),
            color=(0.941, 0.902, 0.824, 1)
        )
        
        def on_select(instance):
            if file_chooser.selection:
                if file_type == 'epub':
                    self.epub_path = file_chooser.selection[0]
                    self.epub_path_label.text = Path(self.epub_path).name
                else:
                    self.style_path = file_chooser.selection[0]
                    self.style_path_label.text = Path(self.style_path).name
            modal.dismiss()
        
        select_btn.bind(on_release=on_select)
        cancel_btn.bind(on_release=modal.dismiss)
        
        btn_layout.add_widget(select_btn)
        btn_layout.add_widget(cancel_btn)
        
        layout.add_widget(title)
        layout.add_widget(file_chooser)
        layout.add_widget(btn_layout)
        
        panel.add_widget(layout)
        modal.add_widget(panel)
        modal.open()
    
    def create_project(self, instance):
        app = App.get_running_app()
        name = self.name_input.text.strip()
        
        if not name:
            self.show_error("Please enter a project name")
            return
        
        if not self.epub_path:
            self.show_error("Please select an EPUB file")
            return
        
        if not self.style_path:
            self.show_error("Please select a style reference file")
            return
        
        success, message = app.create_new_project(name, self.epub_path, self.style_path)
        
        if success:
            self.show_success(message)
            Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'projects'), 2)
        else:
            self.show_error(message)
    
    def show_error(self, message):
        self.show_notification(message, error=True)
    
    def show_success(self, message):
        self.show_notification(message, error=False)
    
    def show_notification(self, message, error=False):
        """Show a premium notification"""
        notification = Label(
            text=message,
            size_hint=(None, None),
            size=(dp(400), dp(60)),
            pos_hint={'center_x': 0.5, 'top': 0.95},
            font_size=dp(16),
            color=(1, 0.3, 0.3, 1) if error else (0.3, 1, 0.3, 1)
        )
        
        self.add_widget(notification)
        
        # Fade out animation
        anim = Animation(opacity=0, duration=2)
        anim.bind(on_complete=lambda *args: self.remove_widget(notification))
        anim.start(notification)


class ProcessingScreen(Screen):
    """Main processing screen with real-time feedback"""
    
    current_log = StringProperty('')
    progress = NumericProperty(0)
    is_processing = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.setup_ui, 0)
    
    def setup_ui(self, dt):
        layout = FloatLayout()
        
        # Main panel
        main_panel = GlassPanel(
            size_hint=(0.95, 0.95),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        content = BoxLayout(
            orientation='vertical',
            padding=dp(30),
            spacing=dp(20)
        )
        
        # Header
        header = BoxLayout(
            size_hint_y=None,
            height=dp(60),
            spacing=dp(20)
        )
        
        back_btn = AnimatedButton(
            text='← Projects',
            size_hint_x=None,
            width=dp(120),
            font_size=dp(16),
            color=(0.941, 0.902, 0.824, 1)
        )
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'projects'))
        
        self.project_title = Label(
            text='Project: Loading...',
            font_size=dp(28),
            color=(0.941, 0.902, 0.824, 1)
        )
        
        header.add_widget(back_btn)
        header.add_widget(self.project_title)
        
        # Control panel
        control_panel = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(120),
            spacing=dp(20)
        )
        
        # Processing options
        options_panel = GlassPanel(size_hint_x=0.6)
        options_layout = BoxLayout(
            orientation='vertical',
            padding=dp(15),
            spacing=dp(10)
        )
        
        # Chapter range inputs
        range_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(40))
        
        range_layout.add_widget(Label(text='Chapters:', size_hint_x=None, width=dp(80), color=(0.8, 0.8, 0.8, 1)))
        
        self.start_input = TextInput(
            text='1',
            multiline=False,
            size_hint_x=None,
            width=dp(60),
            font_size=dp(16),
            background_color=(0.1, 0.1, 0.1, 0.7),
            foreground_color=(0.941, 0.902, 0.824, 1)
        )
        
        range_layout.add_widget(self.start_input)
        range_layout.add_widget(Label(text='to', size_hint_x=None, width=dp(30), color=(0.8, 0.8, 0.8, 1)))
        
        self.end_input = TextInput(
            text='0',
            hint_text='0 = all',
            multiline=False,
            size_hint_x=None,
            width=dp(60),
            font_size=dp(16),
            background_color=(0.1, 0.1, 0.1, 0.7),
            foreground_color=(0.941, 0.902, 0.824, 1)
        )
        
        range_layout.add_widget(self.end_input)
        
        options_layout.add_widget(range_layout)
        options_panel.add_widget(options_layout)
        
        # Action buttons
        btn_panel = BoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint_x=0.4
        )
        
        self.process_btn = AnimatedButton(
            text='Start Processing',
            font_size=dp(18),
            color=(0.941, 0.902, 0.824, 1),
            size_hint_y=None,
            height=dp(50)
        )
        self.process_btn.bind(on_release=self.toggle_processing)
        
        self.package_btn = AnimatedButton(
            text='Package EPUB',
            font_size=dp(18),
            color=(0.941, 0.902, 0.824, 1),
            size_hint_y=None,
            height=dp(50)
        )
        self.package_btn.bind(on_release=self.package_epub)
        
        btn_panel.add_widget(self.process_btn)
        btn_panel.add_widget(self.package_btn)
        
        control_panel.add_widget(options_panel)
        control_panel.add_widget(btn_panel)
        
        # Progress bar
        self.progress_bar = ProgressBar(
            max=100,
            size_hint_y=None,
            height=dp(20)
        )
        
        # Log display
        log_panel = GlassPanel()
        
        self.log_display = TextInput(
            text='',
            readonly=True,
            multiline=True,
            font_size=dp(14),
            background_color=(0.05, 0.05, 0.05, 0.9),
            foreground_color=(0.8, 0.8, 0.8, 1),
            font_name='RobotoMono-Regular'
        )
        
        log_panel.add_widget(self.log_display)
        
        # Assemble layout
        content.add_widget(header)
        content.add_widget(control_panel)
        content.add_widget(self.progress_bar)
        content.add_widget(log_panel)
        
        main_panel.add_widget(content)
        layout.add_widget(main_panel)
        
        self.add_widget(layout)
        
        self.bind(current_log=self.update_log_display)
    
    def on_enter(self):
        """Called when screen is entered"""
        app = App.get_running_app()
        if app.current_project:
            self.project_title.text = f'Project: {app.current_project}'
            self.load_project_status()
    
    def load_project_status(self):
        """Load and display current project status"""
        app = App.get_running_app()
        try:
            project = ProjectManager(app.current_project)
            project.display_status()  # This would need modification to return data
        except Exception as e:
            self.add_log(f"Error loading project status: {e}")
    
    def toggle_processing(self, instance):
        if not self.is_processing:
            self.start_processing()
        else:
            self.stop_processing()
    
    def start_processing(self):
        app = App.get_running_app()
        
        try:
            start = int(self.start_input.text)
            end = int(self.end_input.text) if self.end_input.text else 0
        except ValueError:
            self.add_log("Error: Invalid chapter range")
            return
        
        self.is_processing = True
        self.process_btn.text = 'Stop Processing'
        self.add_log("Starting processing...")
        
        # Create overrides dictionary
        overrides = {
            'start_chapter': start,
            'end_chapter': end
        }
        
        # Start async processing
        app.run_project_async(app.current_project, overrides)
        
        # Start monitoring progress
        Clock.schedule_interval(self.update_progress, 0.5)
    
    def stop_processing(self):
        self.is_processing = False
        self.process_btn.text = 'Start Processing'
        self.add_log("Processing stopped by user")
        Clock.unschedule(self.update_progress)
    
    def update_progress(self, dt):
        """Update progress bar based on project state"""
        app = App.get_running_app()
        try:
            project = ProjectManager(app.current_project)
            state_path = Path(project.project_dir) / 'project_state.json'
            
            with open(state_path) as f:
                state = json.load(f)
            
            total = len(state['chapters'])
            completed = sum(1 for c in state['chapters'].values() if c['status'] == 'completed')
            
            self.progress = (completed / total) * 100 if total > 0 else 0
            self.progress_bar.value = self.progress
            
        except Exception as e:
            pass
    
    def on_processing_complete(self):
        self.is_processing = False
        self.process_btn.text = 'Start Processing'
        self.add_log("Processing completed successfully!")
        Clock.unschedule(self.update_progress)
        self.progress = 100
        self.progress_bar.value = 100
    
    def on_processing_error(self, error_msg):
        self.is_processing = False
        self.process_btn.text = 'Start Processing'
        self.add_log(f"Processing error: {error_msg}")
        Clock.unschedule(self.update_progress)
    
    def package_epub(self, instance):
        app = App.get_running_app()
        self.add_log("Packaging EPUB...")
        
        success, message = app.package_project(app.current_project)
        
        if success:
            self.add_log(f"Success: {message}")
        else:
            self.add_log(f"Error: {message}")
    
    def add_log(self, message):
        # If message already has timestamp from logger, don't add another
        if message.startswith('[') and ']' in message[:10]:
            self.current_log += f"{message}\n"
        else:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.current_log += f"[{timestamp}] {message}\n"
    
    def update_log_display(self, instance, value):
        self.log_display.text = value
        # Auto-scroll to bottom
        self.log_display.cursor = (0, len(value))


class SettingsScreen(Screen):
    """Settings and configuration screen"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.setup_ui, 0)
    
    def setup_ui(self, dt):
        layout = FloatLayout()
        
        # Main panel
        panel = GlassPanel(
            size_hint=(0.8, 0.85),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        content = BoxLayout(
            orientation='vertical',
            padding=dp(40),
            spacing=dp(30)
        )
        
        # Header
        header = BoxLayout(
            size_hint_y=None,
            height=dp(60),
            spacing=dp(20)
        )
        
        back_btn = AnimatedButton(
            text='← Back',
            size_hint_x=None,
            width=dp(120),
            font_size=dp(16),
            color=(0.941, 0.902, 0.824, 1)
        )
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        
        title = Label(
            text='Settings',
            font_size=dp(32),
            color=(0.941, 0.902, 0.824, 1)
        )
        
        header.add_widget(back_btn)
        header.add_widget(title)
        
        # Settings content
        settings_scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(10),
            bar_color=(0.784, 0.608, 0.235, 0.5)
        )
        
        settings_layout = BoxLayout(
            orientation='vertical',
            spacing=dp(20),
            size_hint_y=None,
            padding=[0, dp(20)]
        )
        settings_layout.bind(minimum_height=settings_layout.setter('height'))
        
        # API Configuration section
        api_section = self.create_settings_section('API Configuration')
        
        # Provider selection
        provider_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(20)
        )
        
        provider_layout.add_widget(Label(
            text='AI Provider:',
            size_hint_x=None,
            width=dp(150),
            color=(0.8, 0.8, 0.8, 1)
        ))
        
        # Add provider buttons
        providers = ['OpenAI', 'Gemini', 'AIStudio']
        for provider in providers:
            btn = AnimatedButton(
                text=provider,
                font_size=dp(14),
                color=(0.941, 0.902, 0.824, 1)
            )
            provider_layout.add_widget(btn)
        
        api_section.add_widget(provider_layout)
        
        # API Key input
        self.api_key_input = self.create_settings_input('API Key', 'Enter your API key', password=True)
        api_section.add_widget(self.api_key_input)
        
        # Model selection
        self.model_input = self.create_settings_input('Model', 'e.g., gpt-4o or gemini-pro')
        api_section.add_widget(self.model_input)
        
        settings_layout.add_widget(api_section)
        
        # Processing Configuration
        proc_section = self.create_settings_section('Processing Configuration')
        
        self.max_chapters_input = self.create_settings_input('Max Chapters per Run', '0 = unlimited')
        self.rate_limit_input = self.create_settings_input('Rate Limit (req/min)', '10')
        
        proc_section.add_widget(self.max_chapters_input)
        proc_section.add_widget(self.rate_limit_input)
        
        settings_layout.add_widget(proc_section)
        
        # Save button
        save_btn = AnimatedButton(
            text='Save Settings',
            size_hint=(None, None),
            size=(dp(200), dp(60)),
            pos_hint={'center_x': 0.5},
            font_size=dp(18),
            color=(0.941, 0.902, 0.824, 1)
        )
        save_btn.bind(on_release=self.save_settings)
        
        settings_scroll.add_widget(settings_layout)
        
        content.add_widget(header)
        content.add_widget(settings_scroll)
        content.add_widget(save_btn)
        
        panel.add_widget(content)
        layout.add_widget(panel)
        
        self.add_widget(layout)
        
        # Load current settings
        self.load_current_settings()
    
    def create_settings_section(self, title):
        """Create a settings section with title"""
        section = BoxLayout(
            orientation='vertical',
            spacing=dp(15),
            size_hint_y=None
        )
        section.bind(minimum_height=section.setter('height'))
        
        # Section title
        title_label = Label(
            text=title,
            font_size=dp(20),
            color=(0.784, 0.608, 0.235, 1),
            size_hint_y=None,
            height=dp(30),
            halign='left'
        )
        
        # Divider line
        divider = Label(
            size_hint_y=None,
            height=dp(2)
        )
        
        section.add_widget(title_label)
        section.add_widget(divider)
        
        return section
    
    def create_settings_input(self, label, hint, password=False):
        """Create a settings input field"""
        layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(20)
        )
        
        label_widget = Label(
            text=label + ':',
            size_hint_x=None,
            width=dp(200),
            color=(0.8, 0.8, 0.8, 1),
            halign='left'
        )
        
        input_widget = TextInput(
            hint_text=hint,
            multiline=False,
            password=password,
            font_size=dp(16),
            background_color=(0.1, 0.1, 0.1, 0.7),
            foreground_color=(0.941, 0.902, 0.824, 1),
            cursor_color=(0.784, 0.608, 0.235, 1),
            padding=[dp(15), dp(10)]
        )
        
        layout.add_widget(label_widget)
        layout.add_widget(input_widget)
        
        return layout
    
    def load_current_settings(self):
        """Load settings from config file"""
        try:
            config = ConfigManager()
            # Would need to add methods to ConfigManager to get current values
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self, instance):
        """Save settings to config file"""
        # Implementation would save to config.ini
        self.show_notification("Settings saved successfully!")
    
    def show_notification(self, message):
        """Show a notification message"""
        notification = Label(
            text=message,
            size_hint=(None, None),
            size=(dp(300), dp(60)),
            pos_hint={'center_x': 0.5, 'top': 0.95},
            font_size=dp(16),
            color=(0.3, 1, 0.3, 1)
        )
        
        self.add_widget(notification)
        
        # Fade out animation
        anim = Animation(opacity=0, duration=2)
        anim.bind(on_complete=lambda *args: self.remove_widget(notification))
        anim.start(notification)