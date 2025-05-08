import { Queue, QueueOptions } from 'bullmq';
import { createDragonflyClient } from '../utils/dragonfly.client';
import { containsExactlyOneHashtag } from '../utils/hashtag';

type DragonflyQueueOptions = Omit<QueueOptions, 'connection'>;

export class DragonflyQueue extends Queue {
    private constructor(queueName: string, opts?: QueueOptions) {
        super(queueName, opts);
    }

    // Factory method that sanitizes the queue name and prefix for a Dragonfly-backed BullMQ queue.
    static create(queueName: string, opts?: DragonflyQueueOptions): DragonflyQueue {
        const fullQueueName = opts?.prefix ? `${opts.prefix}:${queueName}` : queueName;
        if (!containsExactlyOneHashtag(fullQueueName)) {
            throw new Error('The queue name (with prefix if provided) must contain exactly one hashtag');
        }

        const connection = createDragonflyClient();
        const queueOptions = {
            ...opts,
            connection
        };

        return new DragonflyQueue(queueName, queueOptions);
    }
}
