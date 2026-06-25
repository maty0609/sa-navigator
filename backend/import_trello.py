"""Import Trello board export into SA Navigator database.

Structure mapping:
  - list.name  -> opportunity.client
  - card.name  -> opportunity.project
  - card.comments -> opportunity_updates.text
"""

import json
import re
import uuid
from datetime import datetime

from sqlmodel import Session, select

from app.config import settings
from app.database import engine
from app.models.opportunity import Opportunity, OpportunityStatus
from app.models.opportunity_update import OpportunityUpdate
from app.models.user import User


def get_or_create_importer_user(db: Session) -> User:
    """Get or create a default user for imported records."""
    user = db.exec(
        select(User).where(User.username == "importer")
    ).first()
    if not user:
        from app.services.auth_service import hash_password

        user = User(
            username="importer",
            full_name="System Importer",
            role="admin",
            password_hash=hash_password("imported"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def parse_comment_date(text: str) -> datetime | None:
    """Extract date from Trello comment like '*2026-05-11* — ...'."""
    match = re.match(r"\*(\d{4}-\d{2}-\d{2})\*", text)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%d")
    return None


def main():
    # Read Trello export
    with open("../trello_mc_clients_export.json", "r") as f:
        data = json.load(f)

    board = data["board"]
    print(f"Importing from board: {board['name']}")

    created = 0
    skipped = 0
    updates_created = 0

    with Session(engine) as db:
        importer = get_or_create_importer_user(db)
        print(f"Using importer user: {importer.username} ({importer.id})")

        for list_item in board["lists"]:
            client_name = list_item["name"]
            print(f"\n--- Client: {client_name} ---")

            for card in list_item["cards"]:
                project_name = card["name"].strip('"')  # strip quotes if present

                # Check for duplicates
                existing = db.exec(
                    select(Opportunity).where(
                        Opportunity.client == client_name,
                        Opportunity.project == project_name,
                    )
                ).first()

                if existing:
                    print(f"  SKIP (exists): {project_name}")
                    skipped += 1
                    opp_id = existing.id
                else:
                    print(f"  CREATE: {project_name}")
                    opp = Opportunity(
                        client=client_name,
                        project=project_name,
                        owner="Unknown",
                        status=OpportunityStatus.NEW,
                        created_by=importer.id,
                    )
                    db.add(opp)
                    db.flush()  # get the UUID without committing
                    opp_id = opp.id
                    created += 1

                # Import comments as opportunity updates
                for comment in card.get("comments", []):
                    text = comment["text"]
                    comment_date = parse_comment_date(text)

                    # Clean up the text - remove the date prefix
                    clean_text = re.sub(r"\*\d{4}-\d{2}-\d{2}\*\s*—\s*", "", text).strip()

                    # Check if this update text already exists for this opportunity
                    existing_update = db.exec(
                        select(OpportunityUpdate).where(
                            OpportunityUpdate.opportunity_id == opp_id,
                            OpportunityUpdate.text == clean_text,
                        )
                    ).first()

                    if not existing_update:
                        update = OpportunityUpdate(
                            text=clean_text,
                            opportunity_id=opp_id,
                            created_by=importer.id,
                            created_at=comment_date or datetime.utcnow(),
                        )
                        db.add(update)
                        updates_created += 1

        db.commit()

    print(f"\n{'='*50}")
    print(f"Import complete!")
    print(f"  Opportunities created: {created}")
    print(f"  Opportunities skipped: {skipped}")
    print(f"  Updates created: {updates_created}")
    print(f"  Total opportunities: {created + skipped}")


if __name__ == "__main__":
    main()
