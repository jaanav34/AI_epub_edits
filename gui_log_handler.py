"""
GUI Log Handler - Real-time logging integration
Captures backend processing output for display in the GUI
"""

import logging
import queue
from datetime import datetime


class GUILogHandler(logging.Handler):
    """Custom logging handler that sends logs to the GUI"""
    
    def __init__(self, callback=None):
        super().__init__()
        self.callback = callback
        self.log_queue = queue.Queue()
        
        # Set up formatter
        self.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        ))
    
    def emit(self, record):
        """Emit a log record"""
        try:
            msg = self.format(record)
            
            # Add to queue
            self.log_queue.put(msg)
            
            # Call callback if provided
            if self.callback:
                self.callback(msg)
                
        except Exception:
            self.handleError(record)
    
    def get_logs(self):
        """Get all queued logs"""
        logs = []
        while not self.log_queue.empty():
            try:
                logs.append(self.log_queue.get_nowait())
            except queue.Empty:
                break
        return logs


class ProcessingLogger:
    """Enhanced logger for processing feedback"""
    
    def __init__(self, gui_callback=None):
        self.gui_handler = GUILogHandler(callback=gui_callback)
        self.logger = logging.getLogger('ai_epub_processing')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.gui_handler)
        
        # Also add console handler for debugging
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(console_handler)
    
    def log_start(self, project_name):
        """Log processing start"""
        self.logger.info(f"Starting processing for project: {project_name}")
    
    def log_chapter(self, chapter_num, chapter_name):
        """Log chapter processing"""
        self.logger.info(f"Processing Chapter {chapter_num}: {chapter_name}")
    
    def log_progress(self, current, total):
        """Log progress update"""
        percentage = (current / total) * 100 if total > 0 else 0
        self.logger.info(f"Progress: {current}/{total} chapters ({percentage:.1f}%)")
    
    def log_ai_request(self, provider, model):
        """Log AI request"""
        self.logger.info(f"Sending request to {provider} ({model})")
    
    def log_ai_response(self, success, time_taken=None):
        """Log AI response"""
        if success:
            msg = "AI response received successfully"
            if time_taken:
                msg += f" (took {time_taken:.2f}s)"
            self.logger.info(msg)
        else:
            self.logger.error("AI request failed")
    
    def log_error(self, error_msg):
        """Log error"""
        self.logger.error(f"Error: {error_msg}")
    
    def log_complete(self, project_name, time_taken=None):
        """Log processing completion"""
        msg = f"Processing complete for project: {project_name}"
        if time_taken:
            msg += f" (total time: {time_taken:.2f}s)"
        self.logger.info(msg)
    
    def log_packaging(self, project_name):
        """Log packaging start"""
        self.logger.info(f"Packaging EPUB for project: {project_name}")
    
    def log_package_complete(self, output_path):
        """Log packaging completion"""
        self.logger.info(f"EPUB packaged successfully: {output_path}")


# Singleton instance for global access
_processing_logger = None


def get_processing_logger(gui_callback=None):
    """Get or create the processing logger instance"""
    global _processing_logger
    if _processing_logger is None:
        _processing_logger = ProcessingLogger(gui_callback)
    elif gui_callback and _processing_logger.gui_handler.callback != gui_callback:
        # Update callback if provided
        _processing_logger.gui_handler.callback = gui_callback
    return _processing_logger