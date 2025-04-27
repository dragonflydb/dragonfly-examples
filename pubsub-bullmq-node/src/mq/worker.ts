import { Worker, WorkerOptions, Processor } from 'bullmq';
import { createDragonflyClient } from '../utils/dragonfly.client';
import { containsHashtag } from '../utils/hashtag';

type DragonflyWorkerOptions = Omit<WorkerOptions, 'connection'>;
type DragonflyWorkerProcessor = string | URL | null | Processor<any, any, string>;

export class DragonflyWorker extends Worker {
    private constructor(queueName: string, processor?: DragonflyWorkerProcessor, opts?: WorkerOptions) {
        super(queueName, processor, opts);
    }

    // Factory method that sanitizes the queue name and prefix for a Dragonfly-backed BullMQ worker.
    static create(queueName: string, processor?: DragonflyWorkerProcessor, opts?: DragonflyWorkerOptions): DragonflyWorker {
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
        const workerOptions = {
            ...opts,
            connection
        };
        return new DragonflyWorker(queueName, processor, workerOptions);
    }
}
