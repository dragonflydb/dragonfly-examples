import { Queue, QueueOptions } from 'bullmq';
import { createDragonflyClient } from '../utils/dragonfly.client';
import { containsHashtag } from '../utils/hashtag';

type DragonflyQueueOptions = Omit<QueueOptions, 'connection'>;

export class DragonflyQueue extends Queue {
    private constructor(queueName: string, opts?: QueueOptions) {
        super(queueName, opts);
    }

    // Factory method that sanitizes the queue name and prefix for a Dragonfly-backed BullMQ queue.
    static create(queueName: string, opts?: DragonflyQueueOptions): DragonflyQueue {
        if (opts?.prefix) {
            if (!containsHashtag(opts.prefix) || containsHashtag(queueName)) {
                throw new Error('A prefix is provided, it must contain a hashtag while the queue name must not contain a hashtag');
            }
        } else {
            if (!containsHashtag(queueName)) {
                throw new Error(`A prefix is not provided, the queue name must contain a hashtag`);
            }
        }
        const connection = createDragonflyClient();
        const queueOptions = {
            ...opts,
            connection
        };
        return new DragonflyQueue(queueName, queueOptions);
    }
}
