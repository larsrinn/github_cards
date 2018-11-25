# -*- coding: utf-8 -*-

"""Console script for github_cards."""
import datetime
import sys

import click
import github3

from github_cards.exceptions import catch_github_cards_exception, GitHubCardsException
from github_cards.otp_cache import OTPCache
from github_cards.rendering import render_cards


@click.command()
@click.argument("owner")
@click.argument("repository")
@click.option(
    "-u",
    "--username",
    help="Username to perform authenticated requests with. "
    "If provided, the script will request the password.",
)
@click.option(
    "-p",
    "--password",
    help="Password for the username provided. "
    "If the username is set but the password is not provided, "
    "script will request it.",
)
@click.option(
    "-m",
    "--milestone-title",
    help="Limit selected issues to a milestone by the milestone's title. "
    "It will search the repository for that milestone and error if "
    "it's not available.",
)
@click.option(
    "-m#",
    "--milestone-number",
    help="Limit selected issue to a milestone by the milestone's number "
    "(similarly to issue numbers). Will be overwritten by the "
    "milestone title if set.",
)
@click.option(
    "-s",
    "--state",
    default="open",
    type=click.Choice(["all", "open", "closed"]),
    help="Limit to all, open or closed issues. Defaults to open",
)
@click.option("-o", "--output")
@catch_github_cards_exception
def main(
    owner,
    repository,
    username,
    password,
    milestone_title,
    milestone_number,
    state,
    output,
):
    """Console script for github_cards."""
    gh = _get_possibly_authenticated_github(username, password)
    repo = _get_repo(gh, owner=owner, repository=repository)
    if milestone_title is not None:
        milestone_number = _get_milestone_number_from_title(repo, milestone_title)
    issues = repo.issues(milestone=milestone_number, state=state)

    rendered = render_cards(issues)

    if output is None:
        output = _get_default_output(owner, repository)
    with open(output, "w") as file:
        file.write(rendered)

    return 0


def _get_possibly_authenticated_github(username: str, password: str) -> github3.GitHub:
    gh = github3.GitHub()
    if username is not None:
        if password is None:
            password = click.prompt(
                f"Please enter GitHub-Password for {username}", hide_input=True
            )
        gh.login(
            username=username,
            password=password,
            two_factor_callback=OTPCache().otp_callback,
        )
    return gh


def _get_repo(gh: github3.GitHub, owner: str, repository: str):
    try:
        return gh.repository(owner=owner, repository=repository)
    except github3.exceptions.NotFoundError:
        raise GitHubCardsException(
            f"Can't find repository {owner}/{repository}. Maybe you need to authorize"
        )


def _get_milestone_number_from_title(
    repo: github3.repos.repo._Repository, milestone_title: str
):
    milestones = repo.milestones()
    try:
        milestone = [
            milestone for milestone in milestones if milestone.title == milestone_title
        ][0]
    except IndexError:
        raise GitHubCardsException(f"Can't find milestone {milestone_title}", err=True)
    return milestone.number


def _get_default_output(owner: str, repository: str):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d--%H:%M")
    output = f"{owner}-{repository}-{now_str}.html"
    return output


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
