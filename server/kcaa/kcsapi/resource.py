#!/usr/bin/env python

import jsonobject


class Resource(jsonobject.JSONSerializableObject):
    """Resource amount."""

    fuel = jsonobject.JSONProperty('fuel', value_type=int)
    """Fuel."""
    ammo = jsonobject.JSONProperty('ammo', value_type=int)
    """Ammo."""
    steel = jsonobject.JSONProperty('steel', value_type=int)
    """Steel."""
    bauxite = jsonobject.JSONProperty('bauxite', value_type=int)
    """Bauxite."""


class ResourcePercentage(jsonobject.JSONSerializableObject):
    """Resource amount percentage."""

    fuel = jsonobject.ReadonlyJSONProperty('fuel', value_type=float)
    """Fuel relative to the capacity. Ranges 0 to 1."""
    ammo = jsonobject.ReadonlyJSONProperty('ammo', value_type=float)
    """Ammo relative to the capacity. Ranges 0 to 1."""
    steel = jsonobject.ReadonlyJSONProperty('steel', value_type=float)
    """Steel relative to the capacity. Ranges 0 to 1."""
    bauxite = jsonobject.ReadonlyJSONProperty('bauxite', value_type=float)
    """Bauxite relative to the capacity. Ranges 0 to 1."""
