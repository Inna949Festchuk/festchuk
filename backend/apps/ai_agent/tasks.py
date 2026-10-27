"""
Celery tasks for AI Agent — GitHub sync and embedding generation.
"""
import logging
import requests

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_project_readme(self, project_id):
    """
    Download README.md from GitHub for a project and update embeddings.
    """
    from apps.projects.models import Project
    from apps.ai_agent.services.rag import RAGService

    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        logger.warning(f"Project {project_id} not found")
        return

    if not project.github_url:
        return

    # Extract repo URL
    github_url = project.github_url.rstrip('/')
    readme_url = f"{github_url}/raw/main/README.md"

    try:
        response = requests.get(readme_url, timeout=30)
        if response.status_code == 200:
            project.readme_content = response.text
            project.save(update_fields=['readme_content'])
            logger.info(f"Updated README for project {project.title}")

            # Regenerate embeddings
            rag = RAGService()
            rag.embed_document(
                text=project.readme_content,
                source_type='project',
                source_id=project.pk,
                metadata={
                    'title': project.title,
                    'technologies': project.technologies,
                },
            )
        else:
            logger.warning(f"GitHub returned {response.status_code} for {readme_url}")

    except Exception as e:
        logger.error(f"Error syncing README for project {project_id}: {e}")
        raise self.retry(exc=e)


@shared_task
def generate_post_embeddings(post_id):
    """
    Generate embeddings for a blog post.
    """
    from apps.blog.models import Post
    from apps.ai_agent.services.rag import RAGService

    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        logger.warning(f"Post {post_id} not found")
        return

    try:
        rag = RAGService()
        rag.embed_document(
            text=post.content,
            source_type='blog_post',
            source_id=post.pk,
            metadata={
                'title': post.title,
                'tags': post.tags,
            },
        )
        logger.info(f"Generated embeddings for post {post.title}")
    except Exception as e:
        logger.error(f"Error generating embeddings for post {post_id}: {e}")
        raise


@shared_task
def sync_all_projects_readme():
    """
    Periodic task: sync all project READMEs from GitHub (daily).
    """
    from apps.projects.models import Project

    projects = Project.objects.filter(github_url__gt='')
    logger.info(f"Syncing READMEs for {projects.count()} projects")

    for project in projects:
        sync_project_readme.delay(project.pk)
