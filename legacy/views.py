from django.shortcuts import redirect, render, get_object_or_404

from catalog.collection.models import Collection
from .models import *
from catalog.models import Item
from django.utils.baseconv import base62


def book(request, id):
    link = get_object_or_404(BookLink, old_id=id)
    return redirect(f"/book/{base62.encode(link.new_uid.int)}")


def movie(request, id):
    link = get_object_or_404(MovieLink, old_id=id)
    return redirect(f"/movie/{base62.encode(link.new_uid.int)}")


def album(request, id):
    link = get_object_or_404(AlbumLink, old_id=id)
    return redirect(f"/album/{base62.encode(link.new_uid.int)}")


def song(request, id):
    link = get_object_or_404(SongLink, old_id=id)
    return redirect(f"/album/{base62.encode(link.new_uid.int)}")


def game(request, id):
    link = get_object_or_404(GameLink, old_id=id)
    return redirect(f"/game/{base62.encode(link.new_uid.int)}")


def collection(request, id):
    link = get_object_or_404(CollectionLink, old_id=id)
    return redirect(f"/collection/{base62.encode(link.new_uid.int)}")


def book_review(request, id):
    link = get_object_or_404(ReviewLink, module="book", old_id=id)
    return redirect(f"/review/{base62.encode(link.new_uid.int)}")


def movie_review(request, id):
    link = get_object_or_404(ReviewLink, module="movie", old_id=id)
    return redirect(f"/review/{base62.encode(link.new_uid.int)}")


def album_review(request, id):
    link = get_object_or_404(ReviewLink, module="album", old_id=id)
    return redirect(f"/review/{base62.encode(link.new_uid.int)}")


def song_review(request, id):
    link = get_object_or_404(ReviewLink, module="song", old_id=id)
    return redirect(f"/review/{base62.encode(link.new_uid.int)}")


def game_review(request, id):
    link = get_object_or_404(ReviewLink, module="game", old_id=id)
    return redirect(f"/review/{base62.encode(link.new_uid.int)}")
