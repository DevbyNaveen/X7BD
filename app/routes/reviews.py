"""
Menu Reviews API Routes
Customer review and rating management for menu items
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from ..services.database import get_database_service

router = APIRouter(prefix="/api/v1/reviews", tags=["Menu Reviews"])


# ============================================================================
# REVIEW MODELS
# ============================================================================

class ReviewCreate(BaseModel):
    menu_item_id: UUID
    customer_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    review_text: Optional[str] = Field(None, max_length=1000)
    is_verified: bool = False


class ReviewResponse(BaseModel):
    id: UUID
    business_id: UUID
    menu_item_id: UUID
    customer_id: Optional[UUID]
    order_id: Optional[UUID]
    rating: int
    review_text: Optional[str]
    is_verified: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime


class ReviewStats(BaseModel):
    total_reviews: int
    average_rating: float
    rating_distribution: Dict[str, int]  # {"1": 5, "2": 3, "3": 10, "4": 15, "5": 20}


# ============================================================================
# REVIEW ENDPOINTS
# ============================================================================

@router.post("/{business_id}", response_model=ReviewResponse)
async def create_review(
    business_id: UUID,
    review_data: ReviewCreate
):
    """
    Create a new menu item review
    """
    try:
        db = get_database_service()
        
        # Verify menu item exists and belongs to business
        menu_item_result = db.client.table("menu_items").select("id").eq("id", str(review_data.menu_item_id)).eq("business_id", str(business_id)).execute()
        if not menu_item_result.data:
            raise HTTPException(status_code=404, detail="Menu item not found")
        
        # Check if customer already reviewed this item
        if review_data.customer_id:
            existing_review = db.client.table("menu_item_reviews").select("id").eq("customer_id", str(review_data.customer_id)).eq("menu_item_id", str(review_data.menu_item_id)).execute()
            if existing_review.data:
                raise HTTPException(status_code=400, detail="Customer has already reviewed this item")
        
        # Create review
        review_data_dict = {
            "business_id": str(business_id),
            "menu_item_id": str(review_data.menu_item_id),
            "customer_id": str(review_data.customer_id) if review_data.customer_id else None,
            "order_id": str(review_data.order_id) if review_data.order_id else None,
            "rating": review_data.rating,
            "review_text": review_data.review_text,
            "is_verified": review_data.is_verified,
            "is_public": True
        }
        
        result = db.client.table("menu_item_reviews").insert(review_data_dict).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create review")
        
        return ReviewResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create review: {str(e)}")


@router.get("/{business_id}/stats", response_model=ReviewStats)
async def get_review_stats(
    business_id: UUID,
    menu_item_id: Optional[UUID] = None
):
    """
    Get review statistics for business or specific menu item
    """
    try:
        db = get_database_service()
        
        # Build query
        query = db.client.table("menu_item_reviews").select("rating").eq("business_id", str(business_id)).eq("is_public", True)
        
        if menu_item_id:
            query = query.eq("menu_item_id", str(menu_item_id))
        
        result = query.execute()
        reviews = result.data if result.data else []
        
        if not reviews:
            return ReviewStats(
                total_reviews=0,
                average_rating=0.0,
                rating_distribution={"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
            )
        
        # Calculate stats
        total_reviews = len(reviews)
        average_rating = sum(review["rating"] for review in reviews) / total_reviews
        
        # Count rating distribution
        rating_distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        for review in reviews:
            rating = str(review["rating"])
            rating_distribution[rating] += 1
        
        return ReviewStats(
            total_reviews=total_reviews,
            average_rating=round(average_rating, 2),
            rating_distribution=rating_distribution
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get review stats: {str(e)}")


@router.get("/{business_id}/item/{menu_item_id}", response_model=List[ReviewResponse])
async def get_item_reviews(
    business_id: UUID,
    menu_item_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get reviews for a specific menu item
    """
    try:
        db = get_database_service()
        
        result = db.client.table("menu_item_reviews").select("*").eq("business_id", str(business_id)).eq("menu_item_id", str(menu_item_id)).eq("is_public", True).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        reviews = result.data if result.data else []
        return [ReviewResponse(**review) for review in reviews]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get item reviews: {str(e)}")


@router.delete("/{business_id}/{review_id}")
async def delete_review(
    business_id: UUID,
    review_id: UUID
):
    """
    Delete a review (admin only)
    """
    try:
        db = get_database_service()
        
        # Verify review exists and belongs to business
        review_result = db.client.table("menu_item_reviews").select("id").eq("id", str(review_id)).eq("business_id", str(business_id)).execute()
        if not review_result.data:
            raise HTTPException(status_code=404, detail="Review not found")
        
        # Delete review
        db.client.table("menu_item_reviews").delete().eq("id", str(review_id)).execute()
        
        return {"message": "Review deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete review: {str(e)}")
