from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup

class PopupBox(Popup):
    pop_up_text = ObjectProperty()
    status_text = ObjectProperty()
    message = ''
    def update_pop_up_text(self, p_message):
        self.message = p_message
        self.pop_up_text.text = p_message
    def update_status(self, status):
        self.status_text.text = status