"""Translation key generation for extracted text."""

import re
from pathlib import Path


class KeyGenerator:
    """Generates translation keys based on filename and element type."""

    @staticmethod
    def get_key_prefix(file_path: Path) -> str:
        """
        Generate key prefix from filename.

        Examples:
            overview.twig -> overview
            about-us.html -> about_us
            contact_form.html.twig -> contact_form
        """
        # Get filename without extensions
        name = file_path.name

        # Remove common extensions
        for ext in ['.html.twig', '.twig', '.html', '.htm']:
            if name.lower().endswith(ext):
                name = name[:-len(ext)]
                break

        # Normalize: replace hyphens with underscores, remove special chars
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        name = re.sub(r'_+', '_', name)  # Collapse multiple underscores
        name = name.strip('_').lower()

        return name

    @staticmethod
    def generate_key(prefix: str, element_type: str, index: int) -> str:
        """
        Generate a full translation key.

        Args:
            prefix: File-based prefix (e.g., "overview")
            element_type: Tag name or attribute (e.g., "h2", "alt")
            index: Sequential index for this element type

        Returns:
            Full key like "overview.h2_1"
        """
        # Normalize element type (replace hyphens with underscores for aria-label etc.)
        normalized_type = element_type.replace('-', '_')
        return f"{prefix}.{normalized_type}_{index}"
