import {Elysia} from "elysia";
import {Redis as Dragonfly} from 'ioredis';

import {AdMetadataStore} from "./ads";
import {AdMetadata, UserAdPreferences} from "./types";

const client = new Dragonfly();

const app = new Elysia()
    .decorate("adMetadataCache", new AdMetadataStore(client))
    .get(
        "/ads/:userId",
        async (context) => {
            return await context.adMetadataCache.getAdMetadataListByUserPreference(context.params.userId);
        },
    )
    .post(
        "/ads",
        async (context) => {
            await context.adMetadataCache.createAdMetadata(context.body);
            context.set.status = 201;
            return;
        },
        {body: AdMetadata}
    )
    .post(
        "/ads/preferences",
        async (context) => {
            await context.adMetadataCache.createUserPreference(context.body);
            context.set.status = 201;
            return;
        },
        {body: UserAdPreferences}
    )
    .listen(3000);

console.log(
    `Ad server API is running at ${app.server?.hostname}:${app.server?.port}`
);
