# AI Research Notes (MVP)

A GitHub Pages microblog. Once a day a GitHub Actions workflow asks a model deployed in Microsoft Foundry for a ~1000-word research post, commits it (one post = one commit), and redeploys the site. No repo scanning and no web search yet.

```
index.html                      the microblog page (reads posts/ in the browser)
posts/index.json, posts/*.md    manifest + one markdown file per post
agent/post.py                   calls Foundry, writes the post and manifest entry
.github/workflows/daily-post.yml  schedule, commit, deploy
```

## Setup

**1. GitHub repo.** Create a public repo, push these files to `main`. Go to Settings > Pages and set Source to **GitHub Actions**. Under Settings > Actions > General > Workflow permissions, allow **Read and write**.

**2. Foundry model.** In the Foundry portal, create a project and deploy a model from the catalog. For a first test, pick a GPT or open model: Claude models start with zero quota on new pay-as-you-go subscriptions and need a quota request first. Then set a low tokens-per-minute limit on the deployment and add a budget alert in Azure Cost Management. From the deployment page, copy:
- the **endpoint** in OpenAI-compatible form (typically `https://<resource>.openai.azure.com/openai/v1/`; use whatever the portal's code sample shows),
- an **API key**,
- the **deployment name**.

**3. GitHub secrets and variables.** Settings > Secrets and variables > Actions:
- Secret `FOUNDRY_API_KEY`
- Variables `FOUNDRY_BASE_URL` (the endpoint) and `FOUNDRY_MODEL` (the deployment name)

**4. Test.** Actions tab > **Daily post** > Run workflow. You should see one new commit on `main`, then a deploy. The site is at `https://<owner>.github.io/<repo>/`. Delete the sample post and its line in `posts/index.json` afterwards.

## About the webhook

You don't need one for this MVP. GitHub's cron starts the run and the workflow calls Foundry directly, so nothing external has to call into GitHub. A webhook-style trigger only matters if something outside GitHub should start the run, such as an Azure Logic App or a Function timer. The workflow already accepts that through `repository_dispatch`:

```
curl -X POST https://api.github.com/repos/OWNER/REPO/dispatches \
  -H "Authorization: Bearer $GITHUB_PAT" \
  -H "Accept: application/vnd.github+json" \
  -d '{"event_type":"daily-post"}'
```

Use a fine-grained token limited to this repo with Contents: read and write. Dispatch events only run on the default branch.

## Local preview

```
pip install openai
export FOUNDRY_API_KEY=... FOUNDRY_BASE_URL=... FOUNDRY_MODEL=...
python agent/post.py        # writes a post
python -m http.server       # open http://localhost:8000
```

## Notes

- The workflow deploys Pages itself, which sidesteps the rule that pushes made with the default token don't trigger other workflows.
- Without web search the model writes from memory, so citations can be wrong. The prompt tells it to cite only what it is sure of; treat links as unverified until search is added.
- If you use Claude on Foundry, swap the client in `agent/post.py` for the `anthropic` SDK pointed at the endpoint shown on the deployment page.
- Next steps from the spec: web search tool, repo-aware digest, multiple agents, cost ledger.
