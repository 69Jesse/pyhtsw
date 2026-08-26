// Dumps htsw's language tables as JSON on stdout, read straight from the
// TypeScript source via Node's built-in type stripping (no build needed).
//
//     node scripts/dump_htsw_contract.mjs <path-to-htsw-repo>

import { registerHooks } from 'node:module';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';

// constants.ts imports items.json without an import attribute; inject it.
registerHooks({
    resolve(specifier, context, nextResolve) {
        const resolved = nextResolve(specifier, context);
        if (resolved.url?.endsWith('.json')) {
            return { ...resolved, importAttributes: { type: 'json' } };
        }
        return resolved;
    },
});

const repo = process.argv[2];
if (!repo) {
    console.error('usage: node dump_htsw_contract.mjs <path-to-htsw-repo>');
    process.exit(1);
}

const load = (rel) => import(pathToFileURL(join(repo, rel)).href);

const [schema, limits, specs, helpers, constants] = await Promise.all([
    load('language/src/importjson/schemaSpec.ts'),
    load('language/src/types/limits.ts'),
    load('language/src/types/actionSpecs.ts'),
    load('language/src/htsl/parse/helpers.ts'),
    load('language/src/types/constants.ts'),
]);

const { IMPORT_JSON_SCHEMA, IMPORT_JSON_SCHEMA_DEFINITIONS: defs } = schema;
const { ACTION_LIMITS, CONDITION_LIMITS, getActionLimit } = limits;
const { ACTION_SPECS, CONDITION_SPECS } = specs;
const {
    ACTION_KWS,
    CONDITION_KWS,
    ACTIONS_TO_KWS,
    CONDITIONS_TO_KWS,
    OPERATION_SYMBOLS,
    COMPARISON_SYMBOLS,
    SHORTHANDS,
} = helpers;

// ACTION_SPECS is advisory upstream (only editor tooling reads it), so hold it
// against the parser's own keyword list before trusting it.
const specKws = new Set(ACTION_SPECS.map((s) => s.kw));
const parserKws = new Set(ACTION_KWS);
for (const kw of specKws) {
    if (!parserKws.has(kw)) throw new Error(`spec kw not in parser: ${kw}`);
}
for (const kw of parserKws) {
    if (!specKws.has(kw)) throw new Error(`parser kw has no spec: ${kw}`);
}
const conditionSpecKws = new Set(CONDITION_SPECS.map((s) => s.kw));
for (const kw of conditionSpecKws) {
    if (!CONDITION_KWS.includes(kw)) {
        throw new Error(`condition spec kw not in parser: ${kw}`);
    }
}

// Keywords no AST type maps to are unreachable from emitted programs
// (balanceTeam today); the var-family aliases collapse onto var/teamvar.
const VAR_ALIASES = ['stat', 'globalstat', 'globalvar', 'teamstat', 'teamvar'];
const reachable = new Set([...Object.values(ACTIONS_TO_KWS), ...VAR_ALIASES]);
const deadActionKws = ACTION_KWS.filter((kw) => !reachable.has(kw));

const specFields = (table) =>
    Object.fromEntries(
        table.map((spec) => [
            spec.kw,
            spec.fields.map((field) => ({
                name: field.name,
                kind: field.kind,
                optional: field.optional ?? false,
            })),
        ]),
    );

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
    contractVersion: 2,
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
        gamemodes: [...constants.GAMEMODES],
        locations: [...constants.LOCATIONS],
        potionEffects: [...constants.POTION_EFFECTS],
        lobbies: [...constants.LOBBIES],
        enchantments: [...constants.ENCHANTMENTS],
        damageCauses: [...constants.DAMAGE_CAUSES],
        fishingEnvironments: [...constants.FISHING_ENVIRONMENTS],
        portalTypes: [...constants.PORTAL_TYPES],
        inventorySlots: [...constants.INVENTORY_SLOTS],
        itemProperties: [...constants.ITEM_PROPERTIES],
        itemLocations: [...constants.ITEM_LOCATIONS],
        itemAmounts: [...constants.ITEM_AMOUNTS],
        operations: [...constants.OPERATIONS],
        varOperations: [...constants.VAR_OPERATIONS],
        comparisons: [...constants.COMPARISONS],
    },
    sounds: constants.SOUNDS.map(({ name, path }) => ({ name, path })),
    minecraftItems: constants.MINECRAFT_ITEMS.map((item) => item.name),
    actionSpecs: specFields(ACTION_SPECS),
    conditionSpecs: specFields(CONDITION_SPECS),
    actionsToKws: { ...ACTIONS_TO_KWS },
    conditionsToKws: { ...CONDITIONS_TO_KWS },
    actionNames: { ...constants.ACTION_NAMES },
    conditionNames: { ...constants.CONDITION_NAMES },
    placeholderSpecs: constants.PLACEHOLDER_SPECS.map((spec) => ({
        name: spec.name,
        valueType: spec.valueType,
        args: spec.args,
    })),
    operationSymbols: { ...OPERATION_SYMBOLS },
    comparisonSymbols: { ...COMPARISON_SYMBOLS },
    shorthands: [...SHORTHANDS],
    deadActionKws,
    actionLimits: { ...ACTION_LIMITS },
    conditionLimits: { ...CONDITION_LIMITS },
    contextLimits,
};

process.stdout.write(JSON.stringify(contract, null, 2) + '\n');
