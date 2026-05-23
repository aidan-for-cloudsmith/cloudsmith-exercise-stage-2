from __future__ import annotations

from transform_service.transformer import transform_record


def main() -> None:
    """Main entry point for the transform service.
    
    Reads event.jsonl file and processes each line.
    """
    print("Transform service started")


if __name__ == "__main__":
    main()
