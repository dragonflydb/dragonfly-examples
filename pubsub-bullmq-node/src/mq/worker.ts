import { Worker, WorkerOptions, Processor } from 'bullmq';
import { createDragonflyClient } from '../utils/dragonfly.client';
import { containsExactlyOneHashtag } from '../utils/hashtag';

type DragonflyWorkerOptions = Omit<WorkerOptions, 'connection'>;
type DragonflyWorkerProcessor = string | URL | null | Processor<any, any, string>;

export class DragonflyWorker extends Worker {
    private constructor(queueName: string, processor?: DragonflyWorkerProcessor, opts?: WorkerOptions) {
        super(queueName, processor, opts);
    }

    // Factory method that sanitizes the queue name and prefix for a Dragonfly-backed BullMQ worker.
    static create(queueName: string, processor?: DragonflyWorkerProcessor, opts?: DragonflyWorkerOptions): DragonflyWorker {
        const fullQueueName = opts?.prefix ? `${opts.prefix}:${queueName}` : queueName;
        if (!containsExactlyOneHashtag(fullQueueName)) {
            throw new Error('The queue name (with prefix if provided) must contain exactly one hashtag');
        }

        const connection = createDragonflyClient();
        const workerOptions = {
            ...opts,
            connection
        };

        return new DragonflyWorker(queueName, processor, workerOptions);
    }
}
