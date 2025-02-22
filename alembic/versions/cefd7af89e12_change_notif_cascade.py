"""change notif cascade

Revision ID: cefd7af89e12
Revises: 2dedd9e6fc8f
Create Date: 2025-02-22 17:59:55.898926

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cefd7af89e12'
down_revision: Union[str, None] = '2dedd9e6fc8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        'notif_chat_account_id_fkey',
        'notif',
        type_='foreignkey'
    )

    op.create_foreign_key(
        'notif_chat_account_id_fkey',
        'notif',
        'chataccount',
        ['chat_account_id'],
        ['id'],
        ondelete='RESTRICT'
    )


def downgrade() -> None:
    op.drop_constraint(
        'notif_chat_account_id_fkey',
        'notif',
        type_='foreignkey'
    )

    op.create_foreign_key(
        'notif_chat_account_id_fkey',
        'notif',
        'chataccount',
        ['chat_account_id'],
        ['id'],
        ondelete='CASCADE'
    )
