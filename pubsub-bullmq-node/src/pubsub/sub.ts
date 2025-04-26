import { Redis as Dragonfly } from 'ioredis';
import { createDragonflyClient } from '../utils/dragonfly.client';

type MessageHandler = (channel: string, message: string) => void;

export class DragonflySubscriber {
    private readonly sub: Dragonfly;
    private readonly channel: string;
    private readonly handler: MessageHandler;

    // Note that a connection can't play both publisher and subscriber roles at the same time.
    // More specifically, when a client issues subscribe() or psubscribe(), it enters the "subscriber" mode.
    // From that point, only commands that modify the subscription set are valid.
    // These commands are: subscribe(), psubscribe(), unsubscribe(), punsubscribe(), ping, and quit().
    // When the subscription set is empty (via unsubscribe/punsubscribe), the connection is put back into the regular mode.
    constructor(channel: string, handler: MessageHandler) {
        const dragonfly = createDragonflyClient();
        this.sub = dragonfly;
        this.channel = channel;
        this.handler = handler;
        this.initialize();
    }

    private initialize() {
        this.sub.on('message', this.handler);
        this.sub.subscribe(this.channel, (err, _) => {
            if (err) {
                console.error(`Failed to subscribe to channel "${this.channel}": ${err.message}`);
                return;
            }
            console.log(`Successfully subscribed to channel "${this.channel}"`);
        });
    }

    close() { this.sub.quit(); }
}
