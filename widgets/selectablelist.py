from kivy.lang import Builder
from kivy.properties import BooleanProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.label import Label
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior

Builder.load_file("kvs/selectable_list.kv")


class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    pass
    ''' Adds selection and focus behaviour to the view. '''


class SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view.       '''
        if is_selected:
            rv.clicked_value(rv.data[index])
        self.selected = is_selected
        if is_selected:
            print("selection changed to {0}".format(rv.data[index]))
        else:
            print("selection removed for {0}".format(rv.data[index]))


class SelectableList(RecycleView):
    def __init__(self, **kwargs):
        super(SelectableList, self).__init__(**kwargs)
        self.returnMethod = None

    def set_data_on_pos(self, index, text):
        self.data[index] = {'text': str(text)}

    def put_data_single(self, data, returnMethod):
        self.set_data(data)
        self.returnMethod = returnMethod

    def clicked_value(self, what):
        self.returnMethod(what)

    def set_data(self, data):
        self.data = [{'text': str(x)} for x in data]
