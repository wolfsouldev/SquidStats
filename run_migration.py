#!/usr/bin/env python
"""Script para ejecutar la migración de la base de datos"""

from database.database import migrate_database, ensure_roles_and_admin

print("Ejecutando migración de base de datos...")
try:
    migrate_database()
    print("✓ Migración completada exitosamente")
except Exception as e:
    print(f"✗ Error durante la migración: {e}")

print("\nAsegurando roles y usuario admin...")
try:
    ensure_roles_and_admin()
    print("✓ Roles y admin verificados correctamente")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n¡Migración finalizada!")
