"""
Code generator utility for customers and suppliers.

Generates sequential codes with prefix:
- Customer: C0001, C0002, C0003, ...
- Supplier: S0001, S0002, S0003, ...
"""

from django.db import models, transaction


class CodeGenerator:
    """
    Sequential code generator for customers and suppliers.

    Format: PREFIX + 4-digit sequence number
    - Customer: C0001, C0002, ...
    - Supplier: S0001, S0002, ...
    """

    @staticmethod
    def generate_customer_code():
        """
        Generate next customer code (C + 4-digit sequence).

        Returns:
            str: Customer code like 'C0001', 'C0002', etc.
        """
        return CodeGenerator._generate_code("C", "customers_customer")

    @staticmethod
    def generate_supplier_code():
        """
        Generate next supplier code (S + 4-digit sequence).

        Returns:
            str: Supplier code like 'S0001', 'S0002', etc.
        """
        return CodeGenerator._generate_code("S", "suppliers_supplier")

    @staticmethod
    def _generate_code(prefix, model_name):
        """
        Generate next sequential code with given prefix.

        Args:
            prefix (str): Code prefix ('C' for customer, 'S' for supplier)
            model_name (str): Django model name for querying max code

        Returns:
            str: Generated code like 'C0001', 'S0001', etc.
        """
        import re

        from django.apps import apps

        # Get the model
        app_label, model_name_only = model_name.split("_", 1)
        model = apps.get_model(app_label=app_label, model_name=model_name_only)

        with transaction.atomic():
            # Find all codes that match pattern: prefix + exactly 4 digits
            pattern = rf"^{prefix}\d{{4}}$"

            existing_codes = model.objects.filter(code__regex=pattern).values_list(
                "code", flat=True
            )

            max_number = 0
            for code in existing_codes:
                try:
                    # Extract the numeric part (remove prefix)
                    num_str = code[len(prefix) :]
                    # Convert to integer
                    num = int(num_str)
                    if num > max_number:
                        max_number = num
                except (ValueError, IndexError):
                    # Skip invalid codes
                    continue

            # Next number is max + 1
            next_number = max_number + 1

            # Format as 4-digit number with leading zeros
            sequence_str = str(next_number).zfill(4)

            # Combine prefix and sequence
            new_code = f"{prefix}{sequence_str}"

            return new_code
