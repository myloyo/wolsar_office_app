"""Task collaboration and explicit weekly state; existing task data is preserved."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "tasks", sa.Column("coexecutor_ids", sa.JSON, nullable=False, server_default="[]")
    )
    op.add_column("tasks", sa.Column("observer_ids", sa.JSON, nullable=False, server_default="[]"))
    op.add_column("tasks", sa.Column("result", sa.Text, nullable=False, server_default=""))
    op.add_column("tasks", sa.Column("version", sa.Integer, nullable=False, server_default="1"))
    op.create_table(
        "task_comments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("task_id", sa.Integer, sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("author_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_task_comments_task_id", "task_comments", ["task_id"])
    op.create_table(
        "task_checklist",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("task_id", sa.Integer, sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("done", sa.Boolean, nullable=False),
    )
    op.create_index("ix_task_checklist_task_id", "task_checklist", ["task_id"])
    op.create_table(
        "week_states",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("week", sa.Date, primary_key=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revision", sa.Integer, nullable=False, server_default="1"),
    )
    op.execute(
        sa.text(
            "INSERT INTO week_states (user_id, week, revision) "
            "SELECT user_id, week, 1 FROM week_items UNION "
            "SELECT user_id, week, 1 FROM week_reviews"
        )
    )


def downgrade():
    op.drop_table("week_states")
    op.drop_index("ix_task_checklist_task_id", table_name="task_checklist")
    op.drop_table("task_checklist")
    op.drop_index("ix_task_comments_task_id", table_name="task_comments")
    op.drop_table("task_comments")
    with op.batch_alter_table("tasks") as batch:
        for column in ("version", "result", "observer_ids", "coexecutor_ids"):
            batch.drop_column(column)
