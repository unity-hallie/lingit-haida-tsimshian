# Lingít · X̱aad Kíl · Smʼalgyax

AI-assisted language learning for three languages of Southeast Alaska.

Built for X̱ʼunei Lance Twitchell and the language communities of Lingít,
Haida, and Tsimshian peoples.

## What this is

Three of the most complex and endangered languages on the Northwest Coast.
Fewer than ten high-fluency speakers of each remain.

This project builds interactive learning tools — starting with vocabulary
and working toward verb morphology — that run **locally, offline, without
subscription costs**, on hardware the communities own.

No one profits from these languages except the people they belong to.

## Languages

- **Lingít** — Na-Dene family. 54,000 square miles of territory across
  southeast Alaska, northwestern British Columbia, and southwestern Yukon.
  Polysynthetic. The verb encodes subject, object, transitivity, mood,
  time, and certainty in a single word.

- **X̱aad Kíl** — Language isolate. Kaigani in southern Prince of Wales,
  Alaska; Haida Gwaii in British Columbia. Fewer than five high-fluency
  birth speakers in the world.

- **Smʼalgyax** — Northwest coast of British Columbia and southeast Alaska.
  Two writing systems. A community gaining momentum.

## What's here now

- **Verb builder**: 978 Tlingit verb themes from Eggleston (2013), searchable by English
- **Structural analysis**: decompose any verb theme — prefixes, classifier, conjugation class, verb type
- **Corpus examples**: 24 narrative texts from the Crippen corpus (Dauenhauer et al.) with translations
- **Honest gaps**: stem alternation and prefix contraction are unpredictable and must come from native speakers — the tool names this rather than papering over it

```
python -m tlingit.builder "go"
python -m tlingit.builder "eat"
python -m tlingit.builder --root aat
```

## Research directions

**Transfer learning hypothesis**: agglutinative base models may generalize better
to polysynthetic languages than English-pretrained models. A model trained on
Finnish or Hungarian already knows that words are built from meaningful ordered
pieces — the same structural intuition Tlingit requires. English teaches lookup;
agglutinative languages teach composition.

Candidate experiment: fine-tune a Hungarian or Finnish base model on Tlingit and
measure how many examples are needed to reach fluent verb conjugation, compared
to an English baseline. If the hypothesis holds, this tells you the minimum viable
corpus size for a working Tlingit model — directly useful for revitalization work.

## Built on

[otter-centaur](https://github.com/unity-hallie/otter-centaur) —
a combinatorial search engine with causal encoding. The Otter loop
doesn't know it's doing language learning. It just combines things
and sees what survives.

## License

Language communities: full sovereignty. Use it however you want.
It's yours.

Everyone else: non-commercial. See LICENSE.

## Contact

Hallie Larsson, Unity Environmental University
X̱ʼunei Lance Twitchell, University of Alaska Southeast
