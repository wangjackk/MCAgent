import { Injectable } from '@nestjs/common';
import { Message } from './schemas/message.schema';
import { MessageRepositoryService } from './repository/message.repo';
@Injectable()
export class MessageService {
  constructor(private readonly messageRepo: MessageRepositoryService) {}

  async addMessage(message: any): Promise<Message> {
    return this.messageRepo.addMessage(
      message.message_id,
      message.message,
      message.from_member_id,
      message.chat_id,
      message.message_type,
      message.timestamp,
    );
  }

  async getMessage(message_id: string): Promise<Message | null> {
    return this.messageRepo.getMessage(message_id);
  }

  async getMessages(message_ids: string[]): Promise<Message[]> {
    return this.messageRepo.getMessages(message_ids);
  }
}
