from flask_wtf import FlaskForm
from wtforms import RadioField, SelectField, StringField
from wtforms.validators import InputRequired, Length, Optional


class ThingForm(FlaskForm):
    name = StringField(
        "Name",
        validators=[
            InputRequired(message="Enter a name"),
            Length(max=32, message="Name must be 32 characters or fewer"),
        ],
        description="Must be 32 characters or fewer.",
    )
    colour = RadioField(
        "Colour",
        validators=[InputRequired(message="Select a colour")],
        choices=[
            ("red", "Red"),
            ("green", "Green"),
            ("blue", "Blue"),
            ("yellow", "Yellow"),
            ("orange", "Orange"),
            ("purple", "Purple"),
            ("black", "Black"),
            ("white", "White"),
        ],
    )


class ThingFilterForm(FlaskForm):
    display = RadioField(
        "Display",
        validators=[Optional()],
        choices=[("all", "All Things"), ("mine", "My Things")],
        default="all",
    )
    sort = SelectField(
        "Sort by",
        validators=[InputRequired()],
        choices=[
            ("name", "Name"),
            ("colour", "Colour"),
            ("user_id", "Owner"),
            ("created_at", "Created"),
            ("updated_at", "Updated"),
        ],
        default="name",
    )
    name = StringField("Name", validators=[Optional()])
    colour = RadioField(
        "Colour",
        validators=[Optional()],
        choices=[
            ("", "All"),
            ("red", "Red"),
            ("green", "Green"),
            ("blue", "Blue"),
            ("yellow", "Yellow"),
            ("orange", "Orange"),
            ("purple", "Purple"),
            ("black", "Black"),
            ("white", "White"),
        ],
        default="",
    )
