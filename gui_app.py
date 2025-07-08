#!/usr/bin/env python3
"""
AI EPUB Rewriter - Premium GUI Application
A luxurious, modern interface for the AI_epub_edits tool.
"""

import os
import sys
import asyncio
import threading
from datetime import datetime
import json
from pathlib import Path

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, ListProperty, ObjectProperty
from kivy.animation import Animation
from kivy.uix.effectwidget import EffectWidget
from kivy.uix.effectwidget import EffectBase
from kivy.graphics import RenderContext, Fbo, Color, Rectangle
from kivy.lang import Builder
from kivy.metrics import dp

# Import the backend components
from core.project_manager import ProjectManager
from core.config_manager import ConfigManager
from core.orchestrator import Orchestrator

# Import the GUI logger
from gui_log_handler import get_processing_logger

# Set window properties for premium feel
Window.clearcolor = (0.118, 0.118, 0.118, 1)  # Dark charcoal background
Window.size = (1400, 900)

# Load custom shaders for glassmorphism effect
BLUR_SHADER = """
$HEADER$

uniform sampler2D texture0;
uniform float blur_size;

void main() {
    vec2 tex_coords = tex_coord0;
    vec4 color = vec4(0.0);
    float total = 0.0;
    
    for (float x = -4.0; x <= 4.0; x += 1.0) {
        for (float y = -4.0; y <= 4.0; y += 1.0) {
            float weight = exp(-(x*x + y*y) / 16.0);
            vec2 offset = vec2(x, y) * blur_size / resolution;
            color += texture2D(texture0, tex_coords + offset) * weight;
            total += weight;
        }
    }
    
    gl_FragColor = color / total;
}
"""

# Dynamic background shader
BACKGROUND_SHADER = """
$HEADER$

uniform float time;
uniform vec2 resolution;
uniform vec3 color1;
uniform vec3 color2;
uniform vec3 accent_color;

float noise(vec2 p) {
    return sin(p.x * 10.0) * sin(p.y * 10.0);
}

void main() {
    vec2 uv = gl_FragCoord.xy / resolution;
    
    // Create flowing gradient
    float wave1 = sin(uv.x * 3.0 + time * 0.5) * 0.5 + 0.5;
    float wave2 = sin(uv.y * 2.0 - time * 0.3) * 0.5 + 0.5;
    float wave3 = sin((uv.x + uv.y) * 4.0 + time * 0.7) * 0.5 + 0.5;
    
    // Mix waves for organic movement
    float mixer = wave1 * 0.4 + wave2 * 0.3 + wave3 * 0.3;
    
    // Create color gradient
    vec3 color = mix(color1, color2, mixer);
    
    // Add subtle accent highlights
    float accent_strength = sin(uv.x * 20.0 + time) * sin(uv.y * 15.0 - time * 1.2) * 0.1;
    accent_strength = max(0.0, accent_strength);
    color = mix(color, accent_color, accent_strength);
    
    // Add subtle noise texture
    float n = noise(uv * 100.0) * 0.02;
    color += vec3(n);
    
    gl_FragColor = vec4(color, 1.0);
}
"""

class GlassmorphismEffect(EffectBase):
    """Custom effect for glassmorphism panels"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.glsl = """
        $HEADER$
        
        uniform sampler2D texture0;
        uniform float opacity;
        
        void main() {
            vec4 color = texture2D(texture0, tex_coord0);
            // Add frosted glass effect
            color.rgb = mix(color.rgb, vec3(0.1, 0.1, 0.1), 0.7);
            color.a *= opacity;
            gl_FragColor = color;
        }
        """

class DynamicBackground(EffectWidget):
    """Animated gradient background with reactive transitions"""
    
    color1 = ListProperty([0.08, 0.08, 0.10, 1.0])  # Deep charcoal
    color2 = ListProperty([0.12, 0.10, 0.14, 1.0])  # Slightly purple charcoal
    accent_color = ListProperty([0.784, 0.608, 0.235, 1.0])  # Gold accent
    
    def __init__(self, **kwargs):
        self.canvas = RenderContext(use_parent_projection=True)
        self.canvas.shader.fs = BACKGROUND_SHADER.replace('$HEADER$', self.canvas.shader.fs.split('\n')[0])
        
        super().__init__(**kwargs)
        
        with self.canvas:
            self.fbo = Fbo(size=Window.size)
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=Window.size, texture=self.fbo.texture)
            
        Window.bind(size=self.update_rect)
        Clock.schedule_interval(self.update_shader, 1/60.)
        
    def update_rect(self, *args):
        self.rect.size = Window.size
        self.fbo.size = Window.size
        
    def update_shader(self, dt):
        self.canvas['time'] = Clock.get_boottime()
        self.canvas['resolution'] = list(Window.size)
        self.canvas['color1'] = self.color1[:3]
        self.canvas['color2'] = self.color2[:3]
        self.canvas['accent_color'] = self.accent_color[:3]
        
    def transition_to_theme(self, theme_name, duration=1.5):
        """Smoothly transition background colors based on screen/theme"""
        themes = {
            'home': {
                'color1': [0.08, 0.08, 0.10, 1.0],
                'color2': [0.12, 0.10, 0.14, 1.0]
            },
            'projects': {
                'color1': [0.10, 0.08, 0.12, 1.0],
                'color2': [0.14, 0.10, 0.12, 1.0]
            },
            'processing': {
                'color1': [0.08, 0.10, 0.12, 1.0],
                'color2': [0.10, 0.12, 0.14, 1.0]
            },
            'settings': {
                'color1': [0.12, 0.10, 0.08, 1.0],
                'color2': [0.14, 0.12, 0.10, 1.0]
            }
        }
        
        if theme_name in themes:
            anim1 = Animation(color1=themes[theme_name]['color1'], duration=duration)
            anim2 = Animation(color2=themes[theme_name]['color2'], duration=duration)
            anim1.start(self)
            anim2.start(self)

class PremiumEbookRewriterApp(App):
    """Main application class"""
    
    current_project = StringProperty('')
    projects_list = ListProperty([])
    processing_progress = NumericProperty(0)
    
    def build(self):
        self.title = 'AI EPUB Rewriter - Premium Edition'
        self.icon = 'assets/icon.png'
        
        # Load KV file for UI layout
        Builder.load_file('gui_layout.kv')
        
        # Create screen manager
        self.screen_manager = ScreenManager()
        
        # Create dynamic background
        self.background = DynamicBackground()
        
        # Initialize screens
        self.init_screens()
        
        # Load existing projects
        self.load_projects()
        
        # Root widget setup
        from kivy.uix.floatlayout import FloatLayout
        root = FloatLayout()
        root.add_widget(self.background)
        root.add_widget(self.screen_manager)
        
        return root
    
    def init_screens(self):
        """Initialize all application screens"""
        from gui_screens import (
            HomeScreen, ProjectsScreen, NewProjectScreen,
            ProcessingScreen, SettingsScreen
        )
        
        self.home_screen = HomeScreen(name='home')
        self.projects_screen = ProjectsScreen(name='projects')
        self.new_project_screen = NewProjectScreen(name='new_project')
        self.processing_screen = ProcessingScreen(name='processing')
        self.settings_screen = SettingsScreen(name='settings')
        
        self.screen_manager.add_widget(self.home_screen)
        self.screen_manager.add_widget(self.projects_screen)
        self.screen_manager.add_widget(self.new_project_screen)
        self.screen_manager.add_widget(self.processing_screen)
        self.screen_manager.add_widget(self.settings_screen)
        
        # Bind screen changes to background transitions
        self.screen_manager.bind(current=self.on_screen_change)
    
    def on_screen_change(self, screen_manager, screen):
        """Handle screen transitions and update background"""
        screen_name = screen.name
        self.background.transition_to_theme(screen_name)
    
    def load_projects(self):
        """Load existing projects from the projects directory"""
        projects_dir = Path('projects')
        if projects_dir.exists():
            self.projects_list = [
                p.name for p in projects_dir.iterdir() 
                if p.is_dir() and (p / 'project_state.json').exists()
            ]
    
    def create_new_project(self, name, epub_path, style_path):
        """Create a new project using the backend"""
        try:
            project = ProjectManager(name)
            project.create_new_project(epub_path, style_path)
            self.load_projects()
            return True, "Project created successfully!"
        except Exception as e:
            return False, str(e)
    
    def run_project_async(self, project_name, overrides=None):
        """Run project processing in background thread"""
        # Set up logging callback
        def log_callback(msg):
            Clock.schedule_once(lambda dt: self.processing_screen.add_log(msg))
        
        # Get logger with GUI callback
        logger = get_processing_logger(log_callback)
        
        def run_in_thread():
            try:
                logger.log_start(project_name)
                
                project = ProjectManager(project_name)
                config = ConfigManager()
                
                # Get start and end chapters from overrides
                start_chapter = overrides.get('start_chapter', 1) if overrides else 1
                end_chapter = overrides.get('end_chapter', 0) if overrides else 0
                
                orchestrator = Orchestrator(project, config, overrides or {})
                
                # Run the async pipeline
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    orchestrator.run_pipeline(
                        start_chapter=start_chapter,
                        end_chapter=end_chapter
                    )
                )
                
                # Schedule UI update on main thread
                Clock.schedule_once(lambda dt: self.on_processing_complete(project_name))
                
            except Exception as e:
                logger.log_error(str(e))
                Clock.schedule_once(lambda dt: self.on_processing_error(str(e)))
        
        # Start processing in background thread
        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True
        thread.start()
    
    def on_processing_complete(self, project_name):
        """Handle processing completion"""
        self.processing_screen.on_processing_complete()
    
    def on_processing_error(self, error_msg):
        """Handle processing errors"""
        self.processing_screen.on_processing_error(error_msg)
    
    def package_project(self, project_name):
        """Package the final EPUB"""
        logger = get_processing_logger()
        try:
            logger.log_packaging(project_name)
            project = ProjectManager(project_name)
            project.package_final_epub()
            output_path = project.get_final_epub_path()
            logger.log_package_complete(output_path)
            return True, f"EPUB packaged successfully at: {output_path}"
        except Exception as e:
            logger.log_error(str(e))
            return False, str(e)

if __name__ == '__main__':
    PremiumEbookRewriterApp().run()