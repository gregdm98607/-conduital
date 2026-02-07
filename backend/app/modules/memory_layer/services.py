"""
Memory Layer services

Business logic for memory operations including hydration and retrieval.
"""

import hashlib
import json
from datetime import date
from typing import Optional

from sqlalchemy import and_, or_, cast, String
from sqlalchemy.orm import Session

from app.modules.memory_layer.models import (
    MemoryObject,
    MemoryNamespace,
    MemoryIndex,
    PrefetchRule,
)
from app.modules.memory_layer.schemas import (
    MemoryObjectCreate,
    MemoryObjectUpdate,
    HydrationRequest,
    HydrationResponse,
    MemoryObjectResponse,
)


class MemoryService:
    """Service for memory object operations"""

    @staticmethod
    def calculate_checksum(content: dict) -> str:
        """Calculate SHA256 checksum of content"""
        content_str = json.dumps(content, sort_keys=True)
        return f"sha256:{hashlib.sha256(content_str.encode()).hexdigest()}"

    @staticmethod
    def create_namespace(db: Session, name: str, description: str = None, default_priority: int = 50) -> MemoryNamespace:
        """Create a new namespace"""
        # Extract parent from dot notation
        parts = name.rsplit(".", 1)
        parent = parts[0] if len(parts) > 1 else None

        namespace = MemoryNamespace(
            name=name,
            description=description,
            parent_namespace=parent,
            default_priority=default_priority,
        )
        db.add(namespace)
        db.commit()
        db.refresh(namespace)
        return namespace

    @staticmethod
    def ensure_namespace(db: Session, name: str) -> MemoryNamespace:
        """Get or create a namespace"""
        namespace = db.query(MemoryNamespace).filter(
            MemoryNamespace.name == name
        ).first()

        if not namespace:
            namespace = MemoryService.create_namespace(db, name)

        return namespace

    @staticmethod
    def create_object(
        db: Session,
        data: MemoryObjectCreate,
        user_id: Optional[int] = None
    ) -> MemoryObject:
        """Create a new memory object"""
        # Ensure namespace exists
        MemoryService.ensure_namespace(db, data.namespace)

        # Calculate checksum
        checksum = MemoryService.calculate_checksum(data.content) if data.content else None

        obj = MemoryObject(
            object_id=data.object_id,
            namespace=data.namespace,
            version=data.version,
            priority=data.priority,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            tags=data.tags,
            checksum=checksum,
            storage_type=data.storage_type,
            content=data.content if data.storage_type == "db" else None,
            file_path=data.file_path if data.storage_type == "file" else None,
            user_id=user_id,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update_object(
        db: Session,
        object_id: str,
        data: MemoryObjectUpdate,
        user_id: Optional[int] = None
    ) -> Optional[MemoryObject]:
        """Update a memory object"""
        query = db.query(MemoryObject).filter(MemoryObject.object_id == object_id)
        if user_id:
            query = query.filter(MemoryObject.user_id == user_id)

        obj = query.first()
        if not obj:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if "content" in update_data and update_data["content"]:
            update_data["checksum"] = MemoryService.calculate_checksum(update_data["content"])
            # Bump version patch number
            parts = obj.version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            update_data["version"] = ".".join(parts)

        for key, value in update_data.items():
            setattr(obj, key, value)

        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_object(
        db: Session,
        object_id: str,
        user_id: Optional[int] = None
    ) -> Optional[MemoryObject]:
        """Get a memory object by ID"""
        query = db.query(MemoryObject).filter(MemoryObject.object_id == object_id)
        if user_id:
            query = query.filter(MemoryObject.user_id == user_id)
        return query.first()

    @staticmethod
    def delete_object(
        db: Session,
        object_id: str,
        user_id: Optional[int] = None
    ) -> bool:
        """Delete a memory object"""
        query = db.query(MemoryObject).filter(MemoryObject.object_id == object_id)
        if user_id:
            query = query.filter(MemoryObject.user_id == user_id)

        obj = query.first()
        if not obj:
            return False

        db.delete(obj)
        db.commit()
        return True

    @staticmethod
    def list_objects(
        db: Session,
        namespace: Optional[str] = None,
        min_priority: int = 0,
        active_only: bool = True,
        user_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MemoryObject]:
        """List memory objects with filters"""
        query = db.query(MemoryObject)

        if namespace:
            # Support prefix matching (e.g., "core" matches "core.identity")
            query = query.filter(
                or_(
                    MemoryObject.namespace == namespace,
                    MemoryObject.namespace.like(f"{namespace}.%")
                )
            )

        query = query.filter(MemoryObject.priority >= min_priority)

        if active_only:
            today = date.today()
            query = query.filter(
                and_(
                    MemoryObject.effective_from <= today,
                    or_(
                        MemoryObject.effective_to.is_(None),
                        MemoryObject.effective_to >= today
                    )
                )
            )

        if user_id:
            query = query.filter(MemoryObject.user_id == user_id)

        query = query.order_by(MemoryObject.priority.desc())
        query = query.offset(offset).limit(limit)

        return query.all()

    @staticmethod
    def search_objects(
        db: Session,
        query_text: str,
        namespace: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 50,
    ) -> list[MemoryObject]:
        """Search memory objects across object_id, namespace, tags, and content."""
        search_term = f"%{query_text.lower()}%"

        q = db.query(MemoryObject).filter(
            or_(
                MemoryObject.object_id.ilike(search_term),
                MemoryObject.namespace.ilike(search_term),
                cast(MemoryObject.tags, String).ilike(search_term),
                cast(MemoryObject.content, String).ilike(search_term),
            )
        )

        if namespace:
            q = q.filter(
                or_(
                    MemoryObject.namespace == namespace,
                    MemoryObject.namespace.like(f"{namespace}.%")
                )
            )

        if user_id:
            q = q.filter(MemoryObject.user_id == user_id)

        q = q.order_by(MemoryObject.priority.desc())
        q = q.limit(limit)

        return q.all()


class HydrationService:
    """Service for context hydration operations"""

    @staticmethod
    def hydrate(
        db: Session,
        request: HydrationRequest,
        user_id: Optional[int] = None
    ) -> HydrationResponse:
        """
        Hydrate context based on request parameters.

        Hydration modes:
        - full: All active objects
        - thin: High priority only (priority >= 70)
        - targeted: Specific namespaces only
        """
        as_of = request.as_of_date or date.today()

        query = db.query(MemoryObject).filter(
            MemoryObject.priority >= request.min_priority,
            MemoryObject.effective_from <= as_of,
            or_(
                MemoryObject.effective_to.is_(None),
                MemoryObject.effective_to >= as_of
            )
        )

        if user_id:
            query = query.filter(MemoryObject.user_id == user_id)

        # Apply namespace filter
        if request.namespaces:
            namespace_conditions = []
            for ns in request.namespaces:
                namespace_conditions.append(MemoryObject.namespace == ns)
                namespace_conditions.append(MemoryObject.namespace.like(f"{ns}.%"))
            query = query.filter(or_(*namespace_conditions))

        # Determine hydration mode
        if request.namespaces:
            hydration_mode = "targeted"
        elif request.min_priority >= 70:
            hydration_mode = "thin"
        else:
            hydration_mode = "full"

        # Get total count before limiting
        total_count = query.count()

        # Order by priority and limit
        query = query.order_by(MemoryObject.priority.desc())
        query = query.limit(request.max_objects)

        objects = query.all()

        # Get unique namespaces
        namespaces_included = list(set(obj.namespace for obj in objects))

        return HydrationResponse(
            objects=[MemoryObjectResponse.model_validate(obj) for obj in objects],
            total_count=total_count,
            included_count=len(objects),
            namespaces_included=namespaces_included,
            hydration_mode=hydration_mode,
        )

    @staticmethod
    def get_quick_key(db: Session, key: str) -> Optional[MemoryObject]:
        """Get memory object by quick key"""
        index_entry = db.query(MemoryIndex).filter(MemoryIndex.key == key).first()
        if not index_entry:
            return None

        if index_entry.target_type == "object" and index_entry.target_id:
            return db.query(MemoryObject).filter(
                MemoryObject.id == index_entry.target_id
            ).first()

        return None

    @staticmethod
    def get_prefetch_bundle(db: Session, trigger: str) -> list[MemoryObject]:
        """Get bundle of objects for a prefetch trigger"""
        rule = db.query(PrefetchRule).filter(
            PrefetchRule.trigger == trigger,
            PrefetchRule.is_active == True
        ).first()

        if not rule:
            return []

        objects = db.query(MemoryObject).filter(
            MemoryObject.object_id.in_(rule.bundle)
        ).order_by(MemoryObject.priority.desc()).all()

        return objects
