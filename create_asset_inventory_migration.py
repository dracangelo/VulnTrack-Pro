"""Add asset inventory table and OS fields to targets

Revision ID: add_asset_inventory
Revises: 
Create Date: 2024-12-02 22:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_asset_inventory'
down_revision = None  # Update this if there are previous migrations
branch_labels = None
depends_on = None


def upgrade():
    # Create asset_inventory table
    op.create_table('asset_inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('scan_id', sa.Integer(), nullable=True),
        
        # OS Information
        sa.Column('os_name', sa.String(length=255), nullable=True),
        sa.Column('os_vendor', sa.String(length=255), nullable=True),
        sa.Column('os_family', sa.String(length=100), nullable=True),
        sa.Column('os_accuracy', sa.Integer(), nullable=True),
        sa.Column('os_cpe', sa.Text(), nullable=True),
        
        # Service Information
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('protocol', sa.String(length=10), nullable=True),
        sa.Column('service_name', sa.String(length=100), nullable=True),
        sa.Column('service_product', sa.String(length=255), nullable=True),
        sa.Column('service_version', sa.String(length=100), nullable=True),
        sa.Column('service_extrainfo', sa.String(length=255), nullable=True),
        sa.Column('service_cpe', sa.Text(), nullable=True),
        
        # Banner Information
        sa.Column('banner', sa.Text(), nullable=True),
        sa.Column('banner_grabbed_at', sa.DateTime(), nullable=True),
        
        # Metadata
        sa.Column('discovered_at', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        
        sa.ForeignKeyConstraint(['target_id'], ['targets.id'], ),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add OS summary fields to targets table
    op.add_column('targets', sa.Column('os_name', sa.String(length=255), nullable=True))
    op.add_column('targets', sa.Column('os_cpe', sa.Text(), nullable=True))
    op.add_column('targets', sa.Column('os_last_detected', sa.DateTime(), nullable=True))


def downgrade():
    # Remove OS fields from targets
    op.drop_column('targets', 'os_last_detected')
    op.drop_column('targets', 'os_cpe')
    op.drop_column('targets', 'os_name')
    
    # Drop asset_inventory table
    op.drop_table('asset_inventory')
