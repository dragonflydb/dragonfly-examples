import { Redis as Dragonfly } from 'ioredis';

export const createDragonflyClient = (): Dragonfly => {
    return new Dragonfly({
        host: process.env.DRAGONFLY_HOST || 'localhost',
        port: parseInt(process.env.DRAGONFLY_PORT || '6380', 10),

        // This is required by BullMQ workers.
        maxRetriesPerRequest: null,
    });
};
