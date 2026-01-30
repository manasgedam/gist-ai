"""
Schema Validation Utility

Validates that SQLite schema matches SQLAlchemy models.
Run this at application startup or manually to catch schema drift.

Usage:
    python -m api.validate_schema
"""

import sqlite3
from pathlib import Path
from api.models import Base, Video, Idea
from api.database import DATABASE_URL


def get_sqlite_columns(table_name: str, db_path: str) -> dict:
    """Get actual columns from SQLite database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type
    conn.close()
    return columns


def get_model_columns(model_class) -> dict:
    """Get expected columns from SQLAlchemy model"""
    columns = {}
    for column in model_class.__table__.columns:
        col_type = str(column.type)
        # Normalize type names
        if 'VARCHAR' in col_type or 'TEXT' in col_type or 'STRING' in col_type:
            col_type = 'TEXT'
        elif 'INTEGER' in col_type:
            col_type = 'INTEGER'
        elif 'FLOAT' in col_type:
            col_type = 'REAL'
        elif 'JSON' in col_type:
            col_type = 'JSON'
        columns[column.name] = col_type
    return columns


def validate_table(model_class, db_path: str) -> tuple[bool, list[str]]:
    """Validate a single table schema"""
    table_name = model_class.__tablename__
    
    try:
        db_columns = get_sqlite_columns(table_name, db_path)
    except sqlite3.OperationalError:
        return False, [f"❌ Table '{table_name}' does not exist in database"]
    
    model_columns = get_model_columns(model_class)
    
    issues = []
    
    # Check for missing columns
    for col_name, col_type in model_columns.items():
        if col_name not in db_columns:
            issues.append(f"❌ Column '{table_name}.{col_name}' missing in database (expected {col_type})")
    
    # Check for extra columns (warning only)
    for col_name in db_columns:
        if col_name not in model_columns:
            issues.append(f"⚠️  Column '{table_name}.{col_name}' exists in database but not in model")
    
    return len([i for i in issues if i.startswith('❌')]) == 0, issues


def validate_schema(verbose: bool = True) -> bool:
    """Validate all models against SQLite database"""
    db_path = DATABASE_URL.replace('sqlite:///', '')
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    models_to_check = [Video, Idea]
    all_valid = True
    all_issues = []
    
    for model in models_to_check:
        valid, issues = validate_table(model, db_path)
        if not valid:
            all_valid = False
        all_issues.extend(issues)
    
    if verbose:
        if all_valid and not all_issues:
            print("✅ Schema validation passed - all models match database")
        else:
            print("Schema validation results:")
            for issue in all_issues:
                print(f"  {issue}")
            if not all_valid:
                print("\n❌ Schema validation FAILED - fix required")
                print("\nTo fix missing columns, run:")
                for issue in all_issues:
                    if "missing in database" in issue and "expected" in issue:
                        # Extract table.column and type
                        parts = issue.split("'")
                        if len(parts) >= 2:
                            table_col = parts[1]
                            table, col = table_col.split('.')
                            col_type = issue.split("expected ")[1].rstrip(")")
                            print(f"  sqlite3 {db_path} \"ALTER TABLE {table} ADD COLUMN {col} {col_type};\"")
    
    return all_valid


if __name__ == "__main__":
    import sys
    success = validate_schema(verbose=True)
    sys.exit(0 if success else 1)
