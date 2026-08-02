// Dumps htsw's import.json schema + action/condition limits as JSON on stdout.
// Needs a built htsw checkout (language/dist).
//
//     node scripts/dump_htsw_contract.mjs <path-to-htsw-repo>

import { pathToFileURL } from 'node:url';
import { join } from 'node:path';

const repo = process.argv[2];
if (!repo) {
    console.error('usage: node dump_htsw_contract.mjs <path-to-htsw-repo>');
    process.exit(1);
}

const load = (rel) => import(pathToFileURL(join(repo, rel)).href);

const [schema, limits] = await Promise.all([
    load('language/dist/importjson/schemaSpec.js'),
    load('language/dist/types/limits.js'),
]);

const { IMPORT_JSON_SCHEMA, IMPORT_JSON_SCHEMA_DEFINITIONS: defs } = schema;
const { ACTION_LIMITS, CONDITION_LIMITS, getActionLimit } = limits;

// Enums live inline in the schema definitions; the source consts aren't exported.
const enumOf = (name) => defs[name].enum;
const keysOf = (name) => Object.keys(defs[name].properties);

// Flatten one importable definition into {field: {required, type, enum?}}.
function fields(name) {
    const out = {};
    for (const [field, spec] of Object.entries(defs[name].properties)) {
        const entry = { required: spec.required, kind: spec.kind };
        if (spec.kind === 'ref') entry.ref = spec.ref;
        if (spec.kind === 'array') entry.items = spec.items.ref ?? spec.items.kind;
        if (spec.enum) entry.enum = [...spec.enum];
        if (spec.integer) entry.integer = true;
        if (spec.minimum !== undefined) entry.minimum = spec.minimum;
        if (spec.maximum !== undefined) entry.maximum = spec.maximum;
        if (spec.pattern) entry.pattern = spec.pattern;
        out[field] = entry;
    }
    return out;
}

const IMPORTABLES = {
    functions: 'functionImportable',
    events: 'eventImportable',
    regions: 'regionImportable',
    items: 'itemImportable',
    menus: 'menuImportable',
    teams: 'teamImportable',
    groups: 'groupImportable',
    commands: 'commandImportable',
    npcs: 'npcImportable',
};

// Context rules are functions upstream; probe them so drift in the rule itself
// (not just the table) shows up as a contract change.
const contextLimits = {
    'CONDITIONAL@events': getActionLimit('CONDITIONAL', { importable: 'events' }),
    'CONDITIONAL@functions': getActionLimit('CONDITIONAL', {
        importable: 'functions',
    }),
    'CONDITIONAL@events/random': getActionLimit('CONDITIONAL', {
        importable: 'events',
        nested: 'random',
    }),
    'HEAL@functions/random': getActionLimit('HEAL', {
        importable: 'functions',
        nested: 'random',
    }),
    'KILL@functions/random': getActionLimit('KILL', {
        importable: 'functions',
        nested: 'random',
    }),
    'GIVE_ITEM@functions/random': getActionLimit('GIVE_ITEM', {
        importable: 'functions',
        nested: 'random',
    }),
};

const contract = {
    // Bumped by hand when the shape of this file changes.
    contractVersion: 1,
    topLevel: Object.fromEntries(
        Object.entries(IMPORT_JSON_SCHEMA.properties).map(([k, v]) => [
            k,
            { required: v.required, kind: v.kind },
        ]),
    ),
    importables: Object.fromEntries(
        Object.entries(IMPORTABLES).map(([section, def]) => [section, fields(def)]),
    ),
    nested: {
        functionIcon: fields('functionIcon'),
        menuSlot: fields('menuSlot'),
        npcEquipment: fields('npcEquipment'),
        pos: fields('pos'),
        bounds: fields('bounds'),
    },
    enums: {
        events: [...defs.eventImportable.properties.event.enum],
        colors: [...enumOf('color')],
        chatSpeeds: [...enumOf('chatSpeed')],
        defaultGameModes: [...enumOf('defaultGameMode')],
        commandModes: [...enumOf('commandMode')],
        npcSkins: [...enumOf('npcSkin')],
        permissions: keysOf('permissions'),
    },
    actionLimits: { ...ACTION_LIMITS },
    conditionLimits: { ...CONDITION_LIMITS },
    contextLimits,
};

process.stdout.write(JSON.stringify(contract, null, 2) + '\n');
