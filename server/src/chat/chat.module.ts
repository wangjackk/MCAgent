import { Module } from '@nestjs/common';
import { ChatGateway } from './chat.gateway';
import { OnlineMembersService } from './online_members.service';
import { MemberService } from './member.service';
import { ChatService } from './chat.service';
import { MemberRepositoryService } from './repository/member.repo';
import { ChatRepositoryService } from './repository/chat.repo';
import { MessageRepositoryService } from './repository/message.repo';
import { MongooseModule } from '@nestjs/mongoose';
import { Member, MemberSchema } from './schemas/member.schema';
import { Chat, ChatSchema } from './schemas/chat.schema';
import { Message, MessageSchema } from './schemas/message.schema';
import { ChatController } from './chat.controller';
import { MessageService } from './message.service';

@Module({
  imports: [
    MongooseModule.forFeature([
      { name: Member.name, schema: MemberSchema },
      { name: Chat.name, schema: ChatSchema },
      { name: Message.name, schema: MessageSchema },
    ]),
  ],
  providers: [
    ChatGateway,
    OnlineMembersService,
    MemberService,
    ChatService,
    MemberRepositoryService,
    ChatRepositoryService,
    MessageRepositoryService,
    MessageService,
  ],
  controllers: [ChatController],
})
export class ChatModule {}
