import { Queue, QueueOptions } from 'bullmq';
import { createDragonflyClient } from '../utils/dragonfly.client';

type DragonflyQueueOptions = Omit<QueueOptions, 'connection'>;

export class DragonflyQueue extends Queue {
    private constructor(queueName: string, opts?: QueueOptions) {
        super(queueName, opts);
    }

    // Factory method that sanitizes the queue name and prefix for a Dragonfly-backed BullMQ queue.
    static create(queueName: string, opts?: DragonflyQueueOptions): DragonflyQueue {
        if (opts?.prefix) {
            if (!this.containsHashtag(opts.prefix) || this.containsHashtag(queueName)) {
                throw new Error('A prefix is provided, it must contain a hashtag while the queue name must not contain a hashtag');
            }
        } else {
            if (!this.containsHashtag(queueName)) {
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

    private static containsHashtag(str: string): boolean {
        const openCount = (str.match(/\{/g) || []).length;
        const closeCount = (str.match(/\}/g) || []).length;
        const openIndex = str.indexOf('{');
        const closeIndex = str.indexOf('}');
        return openCount === 1 && closeCount === 1 && openIndex < closeIndex;
    }
}
