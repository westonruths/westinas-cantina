#!/usr/bin/env python3
"""Fetch public recipe pages and retain only concise recipe-card fields."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse
import json, os, re, tempfile

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "recipes.json"
UA = "WestinasCantinaRecipeImporter/1.0 (+https://westonruths.github.io/westinas-cantina/)"


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def recipe_type(value):
    if isinstance(value, list):
        return any(recipe_type(v) for v in value)
    return str(value or "").lower() == "recipe"


def walk_json(value):
    if isinstance(value, dict):
        if recipe_type(value.get("@type")):
            yield value
        for child in value.values():
            yield from walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)


def instruction_text(value):
    if isinstance(value, str):
        text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
        return clean(text)
    if isinstance(value, dict):
        text = value.get("text") or value.get("name") or value.get("itemListElement")
        return instruction_text(text)
    if isinstance(value, list):
        out=[]
        for child in value:
            text=instruction_text(child)
            if text: out.append(text)
        return out
    return ""


def parse_page(url):
    result={"url":url,"status":"unavailable","error":"","ingredients":[],"steps":[],"yield":"","timings":{}}
    try:
        response=requests.get(url,headers={"User-Agent":UA},timeout=25,allow_redirects=True)
        result["http_status"]=response.status_code
        result["final_url"]=response.url
        soup=BeautifulSoup(response.text,"html.parser")
        candidates=[]
        for tag in soup.find_all("script",attrs={"type":"application/ld+json"}):
            try:
                raw=json.loads(tag.string or tag.get_text())
            except Exception:
                continue
            candidates.extend(walk_json(raw))
        recipe=candidates[0] if candidates else None
        if recipe:
            result["ingredients"]=[clean(x) for x in recipe.get("recipeIngredient",[]) if clean(x)]
            raw_steps=instruction_text(recipe.get("recipeInstructions",[]))
            result["steps"] = raw_steps if isinstance(raw_steps,list) else ([raw_steps] if raw_steps else [])
            result["yield"]=clean(recipe.get("recipeYield"))
            for key in ("prepTime","cookTime","totalTime"):
                if recipe.get(key): result["timings"][key]=clean(recipe[key])
        if not result["ingredients"]:
            result["ingredients"]=[clean(x.get_text(" ",strip=True)) for x in soup.select(".wprm-recipe-ingredient,.recipe-ingredient") if clean(x.get_text(" ",strip=True))]
        if not result["steps"]:
            result["steps"]=[clean(x.get_text(" ",strip=True)) for x in soup.select(".wprm-recipe-instruction-text,.recipe-instruction") if clean(x.get_text(" ",strip=True))]
        if result["ingredients"] or result["steps"]:
            result["status"]="extracted" if result["ingredients"] and result["steps"] else "partial"
        else:
            result["error"]="No recipe ingredients/instructions found in structured data or common recipe markup"
    except Exception as exc:
        result["error"]=f"{type(exc).__name__}: {exc}"
    return result


def main():
    data=json.loads(DATA_PATH.read_text(encoding="utf-8"))
    recipes=data["recipes"]
    targets=[r for r in recipes if r.get("source_url") and not r.get("private_attachment")]
    results=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(parse_page,r["source_url"]):r for r in targets}
        for future in as_completed(futures):
            r=futures[future]
            try: out=future.result()
            except Exception as exc: out={"url":r["source_url"],"status":"unavailable","error":str(exc),"ingredients":[],"steps":[]}
            results.append(out)
    by_url={x["url"]:x for x in results}
    for r in recipes:
        if r.get("source_url") in by_url:
            x=by_url[r["source_url"]]
            r["content_status"]=x["status"]
            r["recipe_ingredients"]=x.get("ingredients",[])
            r["recipe_steps"]=x.get("steps",[])
            r["recipe_yield"]=x.get("yield","")
            r["recipe_timings"]=x.get("timings",{})
            if x.get("error"): r["content_error"]=x["error"]
        elif r.get("private_attachment"):
            r["content_status"]="private_attachment"
            r["recipe_ingredients"]=[]; r["recipe_steps"]=[]
        else:
            r["content_status"]="household_only"
            r["recipe_ingredients"]=[]; r["recipe_steps"]=[]
    data["content_import"]={
        "strategy":"JSON-LD recipe fields first, then common recipe-card markup; story text intentionally excluded",
        "linked_targets":len(targets),
        "extracted":sum(by_url[u]["status"]=="extracted" for u in by_url),
        "partial":sum(by_url[u]["status"]=="partial" for u in by_url),
        "unavailable":sum(by_url[u]["status"]=="unavailable" for u in by_url),
        "updated":"2026-08-29"
    }
    text=json.dumps(data,ensure_ascii=False,indent=2)+"\n"
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=DATA_PATH.parent,delete=False) as f:
        f.write(text); tmp=Path(f.name)
    try:
        json.loads(tmp.read_text(encoding="utf-8")); os.replace(tmp,DATA_PATH)
    finally:
        if tmp.exists(): tmp.unlink()
    print(json.dumps(data["content_import"],indent=2))
    for r in recipes:
        if r.get("content_status") != "extracted": print(r["title"],"|",r.get("content_status"),"|",r.get("content_error",""))

if __name__ == "__main__": main()
