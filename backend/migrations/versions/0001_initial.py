"""Initial office schema."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("leader", sa.String(120), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("roles", sa.JSON, nullable=False),
        sa.Column("department_ids", sa.JSON, nullable=False),
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("creator_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assignee_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("department_id", sa.Integer, sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
    )
    op.create_table(
        "week_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("week", sa.Date, nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("done", sa.Boolean, nullable=False),
    )
    op.create_table(
        "week_reviews",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("week", sa.Date, primary_key=True),
        sa.Column("text", sa.Text, nullable=False),
    )


def downgrade():
    for table in ("week_reviews", "week_items", "tasks", "users", "departments"):
        op.drop_table(table)
