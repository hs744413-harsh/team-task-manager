from django import forms
from django.contrib.auth import get_user_model

from .models import Comment, Project, Task

User = get_user_model()


COLOR_CHOICES = [
    ("indigo", "Indigo"),
    ("emerald", "Emerald"),
    ("amber", "Amber"),
    ("rose", "Rose"),
    ("sky", "Sky"),
    ("violet", "Violet"),
]

ICON_CHOICES = [
    ("folder", "Folder"),
    ("palette", "Design"),
    ("phone", "Mobile"),
    ("plug", "Integration"),
    ("database", "Database"),
    ("shield-check", "Security"),
    ("file-earmark-text", "Docs"),
    ("kanban", "Kanban"),
    ("graph-up", "Analytics"),
]


class _BootstrapFormMixin:
    def _bootstrap(self):
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.TextInput, forms.EmailInput, forms.NumberInput,
                                   forms.URLInput, forms.PasswordInput, forms.DateInput,
                                   forms.Textarea)):
                css = widget.attrs.get("class", "")
                widget.attrs["class"] = (css + " form-control").strip()
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css = widget.attrs.get("class", "")
                widget.attrs["class"] = (css + " form-select").strip()
            elif isinstance(widget, forms.CheckboxInput):
                css = widget.attrs.get("class", "")
                widget.attrs["class"] = (css + " form-check-input").strip()


class ProjectForm(_BootstrapFormMixin, forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"size": "5"}),
        help_text="Hold Ctrl/Cmd to select multiple",
    )
    color = forms.ChoiceField(choices=COLOR_CHOICES, required=False)
    icon = forms.ChoiceField(choices=ICON_CHOICES, required=False)

    class Meta:
        model = Project
        fields = ("name", "description", "status", "priority",
                  "start_date", "due_date", "color", "icon", "members")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3,
                                                 "placeholder": "Describe your project..."}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bootstrap()

    def clean(self):
        data = super().clean()
        start, due = data.get("start_date"), data.get("due_date")
        if start and due and due < start:
            raise forms.ValidationError("Due date cannot be earlier than start date.")
        return data


class TaskForm(_BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Task
        fields = ("project", "title", "description", "status", "priority",
                  "assignee", "due_date")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3,
                                                 "placeholder": "Enter task description"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, project=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            self.fields["project"].initial = project
            self.fields["project"].widget = forms.HiddenInput()
        if user is not None:
            # Members can only assign tasks to themselves; admins can assign anyone.
            if not getattr(user, "is_admin", False) and not user.is_superuser:
                self.fields["assignee"].queryset = User.objects.filter(pk=user.pk)
                self.fields["assignee"].initial = user
        self._bootstrap()


class CommentForm(_BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("body",)
        widgets = {
            "body": forms.Textarea(attrs={"rows": 2, "placeholder": "Add a comment..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bootstrap()


class ProjectMemberAddForm(_BootstrapFormMixin, forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all())

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            existing = project.members.values_list("pk", flat=True)
            self.fields["user"].queryset = User.objects.exclude(pk__in=existing)
        self._bootstrap()
