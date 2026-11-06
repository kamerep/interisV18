# See LICENSE file for full copyright and licensing details
"""Move the property hierarchy off account.asset.parent_id.

Odoo 18 EE uses parent_id/children_ids for gross-increase assets, which
feed the parent's book value and depreciation board. Earlier 18.0 builds of
this module stored the property hierarchy in that column; copy it to
property_parent_id and clear parent_id for property-to-property links.
"""


def migrate(cr, version):
    cr.execute("""
        UPDATE account_asset child
           SET property_parent_id = child.parent_id,
               parent_id = NULL
          FROM account_asset parent
         WHERE child.parent_id = parent.id
           AND child.is_property IS TRUE
           AND parent.is_property IS TRUE
           AND child.property_parent_id IS NULL
    """)
