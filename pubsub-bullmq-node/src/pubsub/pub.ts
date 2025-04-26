import { Redis as Dragonfly } from 'ioredis';
import { createDragonflyClient } from '../utils/dragonfly.client';

export class DragonflyPublisher {
    private pub: Dragonfly;
    private channel: string;

    constructor(channel: string) {
        const dragonfly = createDragonflyClient();
        this.pub = dragonfly;
        this.channel = channel;
    }

    publish(message: string) {
        this.pub.publish(this.channel, message);
    }

    close() { this.pub.quit(); }
}
