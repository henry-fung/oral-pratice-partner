from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models.user import User
from backend.models.vocabulary import Vocabulary
from backend.schemas import VocabularyLookup, VocabularyCreate, VocabularyResponse, MessageResponse
from backend.api.deps import get_current_user
from backend.services.dict_service import dict_service

router = APIRouter(prefix="/api/vocabulary", tags=["单词本"])


@router.post("/lookup", response_model=VocabularyResponse)
async def lookup_word(
    lookup_data: VocabularyLookup,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询单词详情并添加到单词本"""
    # 使用词典 API 查询单词（更快、更准确、免费）
    word_data = dict_service.lookup_word(
        word=lookup_data.word,
        language=lookup_data.language
    )

    # 检查是否已存在
    existing = db.query(Vocabulary).filter(
        Vocabulary.user_id == current_user.id,
        Vocabulary.word == lookup_data.word,
        Vocabulary.language == lookup_data.language
    ).first()

    if existing:
        # 更新现有记录
        existing.definition = word_data.get("definition", existing.definition)
        existing.pronunciation = word_data.get("pronunciation", existing.pronunciation)
        if word_data.get("example_sentence"):
            existing.example_sentence = word_data["example_sentence"]
        db.commit()
        db.refresh(existing)
        return existing

    # 创建新记录
    new_vocab = Vocabulary(
        user_id=current_user.id,
        word=lookup_data.word,
        language=lookup_data.language,
        definition=word_data.get("definition"),
        pronunciation=word_data.get("pronunciation"),
        example_sentence=word_data.get("example_sentence")
    )
    db.add(new_vocab)
    db.commit()
    db.refresh(new_vocab)

    return new_vocab


@router.get("", response_model=List[VocabularyResponse])
async def list_vocabulary(
    page: int = 1,
    limit: int = 20,
    mastered: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单词本列表"""
    query = db.query(Vocabulary).filter(Vocabulary.user_id == current_user.id)

    if mastered is not None:
        query = query.filter(Vocabulary.is_mastered == mastered)

    vocabulary = query.order_by(
        Vocabulary.created_at.desc()
    ).offset((page - 1) * limit).limit(limit).all()

    return vocabulary


@router.post("", response_model=VocabularyResponse)
async def add_vocabulary(
    vocab_data: VocabularyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动添加单词到单词本"""
    # 检查是否已存在
    existing = db.query(Vocabulary).filter(
        Vocabulary.user_id == current_user.id,
        Vocabulary.word == vocab_data.word,
        Vocabulary.language == vocab_data.language
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="单词已存在于单词本中"
        )

    new_vocab = Vocabulary(
        user_id=current_user.id,
        word=vocab_data.word,
        language=vocab_data.language,
        definition=vocab_data.definition,
        pronunciation=vocab_data.pronunciation,
        example_sentence=vocab_data.example_sentence,
        added_from_sentence_id=vocab_data.added_from_sentence_id
    )
    db.add(new_vocab)
    db.commit()
    db.refresh(new_vocab)

    return new_vocab


@router.delete("/{vocab_id}", response_model=MessageResponse)
async def delete_vocabulary(
    vocab_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从单词本删除单词"""
    vocab = db.query(Vocabulary).filter(
        Vocabulary.id == vocab_id,
        Vocabulary.user_id == current_user.id
    ).first()

    if not vocab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="单词不存在"
        )

    db.delete(vocab)
    db.commit()

    return MessageResponse(message="单词已删除")


@router.put("/{vocab_id}/mastered", response_model=VocabularyResponse)
async def mark_vocabulary_mastered(
    vocab_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记单词为已掌握"""
    from datetime import datetime

    vocab = db.query(Vocabulary).filter(
        Vocabulary.id == vocab_id,
        Vocabulary.user_id == current_user.id
    ).first()

    if not vocab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="单词不存在"
        )

    vocab.is_mastered = True
    vocab.review_count += 1
    vocab.last_reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(vocab)

    return vocab
