/* Exact local section commands: never treat arbitrary questions as navigation. */
const JarvisNavigation = {
  destination(text) {
    const value=text.toLowerCase().replace(/[.,!?]/g,'').replace(/\s+/g,' ').trim()
      .replace(/^(?:hey )?jarvis /,'').replace(/^(?:can|could|would|will) you /,'').replace(/^please /,'').replace(/ please$/,'');
    const command=value.replace(/^(?:go|switch|take me) from (?:the )?(?:command(?: center| centre)?|home)(?: page| tab| section)? to /,'go to ');
    const match=command.match(/^(?:open|show me|show|go to|switch to|take me to|navigate to)(?: the)? (.+?)(?: section| tab| page)?$/);
    if(!match)return null;
    const names={command:'command','command center':'command','command centre':'command',home:'command',communications:'communications',transcript:'communications',chat:'communications',projects:'projects',memory:'memory',files:'files',web:'web',diagrams:'diagrams',settings:'settings','change history':'changes',maps:'maps','system status':'system','mission log':'mission','focus and tasks':'focus','focus & tasks':'focus',tasks:'focus',focus:'focus'};
    return names[match[1]]||null;
  }
};
if(typeof module!=='undefined')module.exports=JarvisNavigation;
